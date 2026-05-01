"""Tests for rebuild.application.pipeline."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.application.pipeline import Pipeline
from rebuild.domain.commit import CommitInfo
from rebuild.domain.day_result import DayResult
from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from rebuild.domain.models import DeployMethod, WalkConfig


def _config(tmp_path: Path, dry_run: bool = True) -> WalkConfig:
    return WalkConfig(
        repo_path=tmp_path,
        days=3,
        deploy_method=DeployMethod.NONE,
        dry_run=dry_run,
        output_dir=tmp_path / ".rebuild",
        screenshots=False,
    )


def _commit(day: date = date(2024, 3, 15)) -> CommitInfo:
    # Generate unique SHA based on day to avoid duplicate SHA issues in tests
    day_suffix = day.strftime("%Y%m%d")
    return CommitInfo(
        sha=f"abc123def456abc123def456abc123def{day_suffix}",
        message="Test commit",
        author="Alice",
        timestamp=datetime(2024, 3, 15, 10, 0),
        date=day,
    )


# ──────────────────────────────────────────────
# run — no commits
# ──────────────────────────────────────────────

def test_run_returns_empty_when_no_commits(tmp_path):
    config = _config(tmp_path)
    pipeline = Pipeline(config)
    with patch.object(pipeline.git, "days_with_commits", return_value=[]):
        results = pipeline.run()
    assert results == []


# ──────────────────────────────────────────────
# run_day — dry_run
# ──────────────────────────────────────────────

def test_run_day_dry_run_skips_checkout(tmp_path):
    config = _config(tmp_path, dry_run=True)
    pipeline = Pipeline(config)
    commit = _commit()

    ep = Endpoint(method="GET", path="/api/health", base_url="http://localhost:8003")
    ep_result = EndpointResult(endpoint=ep, status=EndpointStatus.OK, http_status=200)

    with patch.object(pipeline.git, "checkout") as mock_checkout, \
         patch.object(pipeline.deploy, "start", return_value=True), \
         patch.object(pipeline.deploy, "stop"), \
         patch.object(pipeline.scanner, "execute", return_value=[ep]), \
         patch.object(pipeline.tester, "execute", return_value=[ep_result]), \
         patch.object(pipeline.reporter, "save_day"):
        result = pipeline.run_day(date(2024, 3, 15), commit)

    mock_checkout.assert_not_called()
    assert result.deploy_success is True
    assert len(result.endpoint_results) == 1


def test_run_day_returns_day_result(tmp_path):
    config = _config(tmp_path, dry_run=True)
    pipeline = Pipeline(config)
    commit = _commit()

    ep = Endpoint(method="GET", path="/api/health", base_url="http://localhost:8003")
    ep_result = EndpointResult(endpoint=ep, status=EndpointStatus.OK)

    with patch.object(pipeline.deploy, "start", return_value=True), \
         patch.object(pipeline.deploy, "stop"), \
         patch.object(pipeline.scanner, "execute", return_value=[ep]), \
         patch.object(pipeline.tester, "execute", return_value=[ep_result]), \
         patch.object(pipeline.reporter, "save_day"):
        result = pipeline.run_day(date(2024, 3, 15), commit)

    assert isinstance(result, DayResult)
    assert result.day == date(2024, 3, 15)
    assert result.commit.sha == commit.sha
    assert result.duration_seconds >= 0


def test_run_day_deploy_failure_skips_scan(tmp_path):
    config = _config(tmp_path, dry_run=False)
    pipeline = Pipeline(config)
    commit = _commit()

    with patch.object(pipeline.git, "checkout"), \
         patch.object(pipeline.deploy, "start", return_value=False), \
         patch.object(pipeline.deploy, "stop"), \
         patch.object(pipeline.scanner, "execute") as mock_scan, \
         patch.object(pipeline.reporter, "save_day"):
        result = pipeline.run_day(date(2024, 3, 15), commit)

    mock_scan.assert_not_called()
    assert result.deploy_success is False


def test_run_day_stop_always_called(tmp_path):
    config = _config(tmp_path, dry_run=True)
    pipeline = Pipeline(config)
    commit = _commit()

    with patch.object(pipeline.deploy, "start", return_value=True), \
         patch.object(pipeline.deploy, "stop") as mock_stop, \
         patch.object(pipeline.scanner, "execute", side_effect=RuntimeError("scan failed")), \
         patch.object(pipeline.reporter, "save_day"):
        result = pipeline.run_day(date(2024, 3, 15), commit)

    mock_stop.assert_called_once()
    assert result.error is not None


# ──────────────────────────────────────────────
# run — full loop
# ──────────────────────────────────────────────

def test_run_processes_all_days(tmp_path):
    config = _config(tmp_path, dry_run=True)
    pipeline = Pipeline(config)

    commits = [
        (date(2024, 3, 13), _commit(date(2024, 3, 13))),
        (date(2024, 3, 14), _commit(date(2024, 3, 14))),
        (date(2024, 3, 15), _commit(date(2024, 3, 15))),
    ]

    ep = Endpoint(method="GET", path="/api/health", base_url="http://localhost:8003")
    ep_result = EndpointResult(endpoint=ep, status=EndpointStatus.OK)

    with patch.object(pipeline.git, "days_with_commits", return_value=commits), \
         patch.object(pipeline.git, "restore_head"), \
         patch.object(pipeline.deploy, "start", return_value=True), \
         patch.object(pipeline.deploy, "stop"), \
         patch.object(pipeline.scanner, "execute", return_value=[ep]), \
         patch.object(pipeline.tester, "execute", return_value=[ep_result]), \
         patch.object(pipeline.reporter, "save_day"), \
         patch.object(pipeline.reporter, "save_timeline_index"):
        results = pipeline.run()

    assert len(results) == 3
    assert [r.day for r in results] == [date(2024, 3, 13), date(2024, 3, 14), date(2024, 3, 15)]
