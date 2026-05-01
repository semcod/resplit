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


def test_prewarm_worktrees_calls_get_or_create_for_every_sha(tmp_path):
    config = _config(tmp_path)
    pipeline = AcceleratedPipeline(config)

    created = []

    def _fake_get_or_create(sha):
        created.append(sha)

    with patch.object(pipeline.worktrees, "get_or_create", side_effect=_fake_get_or_create):
        pipeline._prewarm_worktrees(["aaa111", "bbb222", "ccc333"])

    assert sorted(created) == ["aaa111", "bbb222", "ccc333"]


def test_prewarm_worktrees_continues_after_individual_failure(tmp_path):
    config = _config(tmp_path)
    pipeline = AcceleratedPipeline(config)

    def _flaky(sha):
        if sha == "bad000":
            raise RuntimeError("lock contention")

    with patch.object(pipeline.worktrees, "get_or_create", side_effect=_flaky):
        # should not raise
        pipeline._prewarm_worktrees(["good111", "bad000", "good222"])


def test_needs_db_restore_returns_true_when_migration_file_changed(tmp_path):
    config = _config(tmp_path)
    pipeline = AcceleratedPipeline(config)

    with patch.object(pipeline.git, "diff_names", return_value=["app/migrations/0001_initial.py", "app/views.py"]):
        assert pipeline._needs_db_restore("sha_prev", "sha_cur") is True


def test_needs_db_restore_returns_false_when_no_db_files_changed(tmp_path):
    config = _config(tmp_path)
    pipeline = AcceleratedPipeline(config)

    with patch.object(pipeline.git, "diff_names", return_value=["app/views.py", "app/serializers.py"]):
        assert pipeline._needs_db_restore("sha_prev", "sha_cur") is False


def test_needs_db_restore_returns_true_when_no_previous_commit(tmp_path):
    config = _config(tmp_path)
    pipeline = AcceleratedPipeline(config)

    assert pipeline._needs_db_restore(None, "sha_cur") is True


def test_needs_db_restore_returns_true_when_diff_fails(tmp_path):
    config = _config(tmp_path)
    pipeline = AcceleratedPipeline(config)

    with patch.object(pipeline.git, "diff_names", return_value=None):
        assert pipeline._needs_db_restore("sha_prev", "sha_cur") is True


def test_run_day_fast_skips_db_restore_when_no_db_files_changed(tmp_path):
    config = _config(tmp_path)
    pipeline = AcceleratedPipeline(config)
    commit = _commit()
    pipeline._baseline_snapshot = "baseline"
    pipeline._previous_commit = "prevsha"

    with patch.object(pipeline.deploy, "switch_commit", return_value=True), \
         patch.object(pipeline.worktrees, "get_active_path", return_value=tmp_path), \
         patch.object(pipeline, "_needs_db_restore", return_value=False) as mock_needs, \
         patch.object(pipeline.db_snapshots, "restore") as mock_restore, \
         patch.object(pipeline.scanner, "execute", return_value=[]), \
         patch.object(pipeline.tester, "execute_sync", return_value=[]), \
         patch.object(pipeline.reporter, "save_day"):
        result = pipeline._run_day_fast(date(2024, 3, 15), commit)

    assert result.error is None
    mock_needs.assert_called_once_with("prevsha", commit.sha)
    mock_restore.assert_not_called()