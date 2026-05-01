from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

from rebuild.application.accelerated_pipeline import AcceleratedPipeline
from rebuild.domain.commit import CommitInfo
from rebuild.domain.models import DeployMethod, WalkConfig


def _config(tmp_path: Path) -> WalkConfig:
    return WalkConfig(
        repo_path=tmp_path,
        output_dir=tmp_path / ".rebuild",
        deploy_method=DeployMethod.DOCKER_COMPOSE,
        screenshots=False,
    )


def _commit(day: date = date(2024, 3, 15)) -> CommitInfo:
    day_suffix = day.strftime("%Y%m%d")
    return CommitInfo(
        sha=f"abc123def456abc123def456abc123def{day_suffix}",
        message="Test commit",
        author="Alice",
        timestamp=datetime(2024, 3, 15, 10, 0),
        date=day,
    )


def test_run_aborts_when_baseline_snapshot_creation_fails(tmp_path):
    config = _config(tmp_path)
    pipeline = AcceleratedPipeline(config)
    commits = [(date(2024, 3, 15), _commit())]

    with patch.object(pipeline.git, "days_with_commits", return_value=commits), \
         patch.object(pipeline, "_prewarm_worktrees"), \
         patch.object(pipeline.worktrees, "get_active_path", return_value=tmp_path / "wt"), \
         patch.object(pipeline.deploy, "prepare_runtime", return_value=True), \
         patch.object(pipeline.deploy, "start", return_value=True), \
         patch.object(pipeline.db_snapshots, "create_baseline", side_effect=RuntimeError("snapshot broken")), \
         patch.object(pipeline.reporter, "save_timeline_index") as mock_report:
        results = pipeline.run()

    assert results == []
    mock_report.assert_not_called()


def test_run_day_fast_stops_when_db_restore_fails(tmp_path):
    config = _config(tmp_path)
    pipeline = AcceleratedPipeline(config)
    commit = _commit()
    pipeline._baseline_snapshot = "baseline"

    with patch.object(pipeline.deploy, "switch_commit", return_value=True), \
         patch.object(pipeline.worktrees, "get_active_path", return_value=tmp_path), \
         patch.object(pipeline.patcher, "apply_manual_overrides", return_value=0), \
         patch.object(pipeline.db_snapshots, "restore", return_value=False), \
         patch.object(pipeline.scanner, "execute") as mock_scan:
        result = pipeline._run_day_fast(date(2024, 3, 15), commit)

    assert result.error == "DB restore failed: baseline"
    mock_scan.assert_not_called()


def test_run_day_fast_stops_when_app_health_fails_after_db_restore(tmp_path):
    config = _config(tmp_path)
    pipeline = AcceleratedPipeline(config)
    commit = _commit()
    pipeline._baseline_snapshot = "baseline"

    with patch.object(pipeline.deploy, "switch_commit", return_value=True), \
         patch.object(pipeline.worktrees, "get_active_path", return_value=tmp_path), \
         patch.object(pipeline.patcher, "apply_manual_overrides", return_value=0), \
         patch.object(pipeline.db_snapshots, "restore", return_value=True), \
         patch.object(pipeline.deploy, "wait_healthy", return_value=False), \
         patch.object(pipeline.scanner, "execute") as mock_scan:
        result = pipeline._run_day_fast(date(2024, 3, 15), commit)

    assert result.error == "App health check failed after DB restore"
    mock_scan.assert_not_called()


def test_run_day_fast_uses_full_health_gate_after_db_restore(tmp_path):
    config = _config(tmp_path)
    pipeline = AcceleratedPipeline(config)
    commit = _commit()
    pipeline._baseline_snapshot = "baseline"

    with patch.object(pipeline.deploy, "switch_commit", return_value=True), \
         patch.object(pipeline.db_snapshots, "restore", return_value=True), \
         patch.object(pipeline.deploy, "wait_healthy", return_value=True) as mock_health, \
            patch.object(pipeline.worktrees, "get_active_path", return_value=tmp_path), \
         patch.object(pipeline.scanner, "execute", return_value=[]), \
         patch.object(pipeline.tester, "execute_sync", return_value=[]), \
         patch.object(pipeline.reporter, "save_day"):
        result = pipeline._run_day_fast(date(2024, 3, 15), commit)

    assert result.error is None
    mock_health.assert_called_once_with()