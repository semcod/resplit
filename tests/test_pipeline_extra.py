"""
Targeted tests for pipeline.py and base_pipeline.py branches.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.domain.models import WalkConfig, DeployMethod
from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from rebuild.domain.commit import CommitInfo
from rebuild.domain.day_result import DayResult
from rebuild.application.base_pipeline import BasePipeline
from rebuild.application.pipeline import Pipeline


def _cfg(tmp_path, dry_run=True, **kw):
    return WalkConfig(
        repo_path=tmp_path,
        output_dir=tmp_path,
        deploy_method=DeployMethod.NONE,
        dry_run=dry_run,
        **kw,
    )


def _commit(day=date(2025, 1, 1)):
    return CommitInfo(sha="abc12345", message="m", author="a", timestamp="t", date=day)


# ─────────────────────────────────────────────────────────────
# BasePipeline
# ─────────────────────────────────────────────────────────────

def test_base_pipeline_processed_shas_persisted(tmp_path):
    cfg = _cfg(tmp_path)
    bp = BasePipeline(cfg)
    bp._processed_shas.add("sha1")
    bp._processed_shas.add("sha2")
    bp._save_state()

    bp2 = BasePipeline(cfg)
    assert "sha1" in bp2._processed_shas
    assert "sha2" in bp2._processed_shas


def test_base_pipeline_emit_creates_jsonl(tmp_path):
    cfg = _cfg(tmp_path)
    bp = BasePipeline(cfg)
    bp._emit("TEST_EVENT", data="hello")
    log = tmp_path / "history.jsonl"
    assert log.exists()
    lines = log.read_text().strip().split("\n")
    assert len(lines) >= 1


def test_base_pipeline_log_delegates_to_console(tmp_path):
    cfg = _cfg(tmp_path)
    mock_console = MagicMock()
    bp = BasePipeline(cfg, console=mock_console)
    bp.log("test message")
    mock_console.print.assert_called_once_with("test message")


# ─────────────────────────────────────────────────────────────
# Pipeline.run — dry run returns empty when no commits
# ─────────────────────────────────────────────────────────────

def test_pipeline_run_no_commits(tmp_path):
    cfg = _cfg(tmp_path)
    p = Pipeline(cfg)
    with patch.object(p.git, "days_with_commits", return_value=[]):
        results = p.run()
    assert results == []


def test_pipeline_run_dry_run_single_commit(tmp_path):
    cfg = _cfg(tmp_path)
    p = Pipeline(cfg)
    day = date(2025, 1, 1)
    commit = _commit(day)

    ep = Endpoint(method="GET", path="/api/health", base_url="http://x")
    er = EndpointResult(endpoint=ep, status=EndpointStatus.OK, http_status=200)
    fake_result = DayResult(
        day=day, commit=commit, deploy_method=DeployMethod.NONE,
        deploy_success=True, endpoints=[ep], endpoint_results=[er],
        output_dir=tmp_path,
    )

    with patch.object(p.git, "days_with_commits", return_value=[(day, commit)]), \
         patch.object(p, "run_day", return_value=fake_result):
        results = p.run()

    assert len(results) == 1
    assert results[0].deploy_success is True


def test_pipeline_run_skips_already_processed(tmp_path):
    cfg = _cfg(tmp_path, dry_run=True)
    p = Pipeline(cfg)
    day = date(2025, 1, 1)
    commit = _commit(day)
    p._processed_shas.add(commit.sha)

    with patch.object(p.git, "days_with_commits", return_value=[(day, commit)]), \
         patch.object(p, "run_day") as mock_run_day:
        results = p.run()

    mock_run_day.assert_not_called()
    assert results == []


# ─────────────────────────────────────────────────────────────
# Pipeline._find_recovery_sha
# ─────────────────────────────────────────────────────────────

def test_check_for_manual_fix_returns_none_when_no_fix(tmp_path):
    cfg = _cfg(tmp_path)
    p = Pipeline(cfg)
    mock_git = MagicMock()
    mock_git.repo_path = tmp_path
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "abc123\tnormal commit message\n"
    mock_git.shell.run.return_value = mock_result
    result = p._check_for_manual_fix(mock_git, "dead1234")
    assert result is None


def test_check_for_manual_fix_finds_fix_commit(tmp_path):
    cfg = _cfg(tmp_path)
    p = Pipeline(cfg)
    mock_git = MagicMock()
    mock_git.repo_path = tmp_path
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "fix123ab\trebuild-fix:dead1234 recover\n"
    mock_git.shell.run.return_value = mock_result
    result = p._check_for_manual_fix(mock_git, "dead1234")
    assert result == "fix123ab"


def test_check_for_manual_fix_ignores_git_error(tmp_path):
    cfg = _cfg(tmp_path)
    p = Pipeline(cfg)
    mock_git = MagicMock()
    mock_git.repo_path = tmp_path
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_git.shell.run.return_value = mock_result
    result = p._check_for_manual_fix(mock_git, "dead1234")
    assert result is None
