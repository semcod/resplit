"""Tests for rebuild.application.services.git_service."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from rebuild.domain.commit import CommitInfo
from rebuild.domain.models import WalkConfig
from rebuild.application.services.git_service import GitService


def test_days_with_commits_parses_log(tmp_path):
    config = WalkConfig(repo_path=tmp_path, days=2)
    service = GitService(tmp_path)
    
    log_output = """476fb9bb77636e08170c406085a6a0907d727b7d|2026-05-01|Initial commit|Tom|2026-05-01T10:00:00+02:00
abc123|2026-05-02|Second commit|Tom|2026-05-02T10:00:00+02:00"""
    
    with patch.object(service, "_run_git", return_value=log_output):
        results = service.days_with_commits(config)
    
    assert len(results) == 2
    assert results[0][0] == date(2026, 5, 1)
    assert results[0][1].sha == "476fb9bb77636e08170c406085a6a0907d727b7d"
    assert results[1][0] == date(2026, 5, 2)


def test_days_with_commits_filters_by_date_range(tmp_path):
    config = WalkConfig(repo_path=tmp_path, days=10, date_from=date(2026, 5, 2), date_to=date(2026, 5, 3))
    service = GitService(tmp_path)
    
    log_output = """476fb9bb77636e08170c406085a6a0907d727b7d|2026-05-01|Initial commit|Tom|2026-05-01T10:00:00+02:00
abc123|2026-05-02|Second commit|Tom|2026-05-02T10:00:00+02:00
def456|2026-05-03|Third commit|Tom|2026-05-03T10:00:00+02:00"""
    
    with patch.object(service, "_run_git", return_value=log_output):
        results = service.days_with_commits(config)
    
    assert len(results) == 2
    assert results[0][0] == date(2026, 5, 2)
    assert results[1][0] == date(2026, 5, 3)


def test_days_with_commits_empty_on_error(tmp_path):
    config = WalkConfig(repo_path=tmp_path, days=2)
    service = GitService(tmp_path)
    
    with patch.object(service, "_run_git", side_effect=RuntimeError("Git error")):
        results = service.days_with_commits(config)
    
    assert results == []


def test_checkout_calls_git(tmp_path):
    service = GitService(tmp_path)
    with patch.object(service, "_run_git") as mock_run:
        service.checkout("abc123")
        mock_run.assert_called_once_with(["checkout", "--force", "--quiet", "abc123"])


def test_restore_head_calls_git(tmp_path):
    service = GitService(tmp_path)
    with patch.object(service, "_run_git") as mock_run:
        service.restore_head()
        mock_run.assert_called_once_with(["checkout", "--force", "--quiet", "HEAD"])


def test_restore_head_with_sha(tmp_path):
    service = GitService(tmp_path)
    with patch.object(service, "_run_git") as mock_run:
        service.restore_head("deadbeef")
        mock_run.assert_called_once_with(["checkout", "--force", "--quiet", "deadbeef"])


def test_clone_for_walk_creates_clone(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"
    service = GitService(src)
    with patch.object(service.shell, "run") as mock_run:
        mock_run.return_value = type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})() 
        clone_svc = service.clone_for_walk(out)
    assert clone_svc.repo_path == out / "repo"


def test_execute_delegates_to_days_with_commits(tmp_path):
    config = WalkConfig(repo_path=tmp_path, days=2)
    service = GitService(tmp_path)
    
    with patch.object(service, "days_with_commits", return_value=[]) as mock_days:
        service.execute(config)
        mock_days.assert_called_once_with(config)
