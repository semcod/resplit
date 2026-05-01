"""Tests for rebuild.git_walker."""
from __future__ import annotations

import subprocess
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.git_walker import get_commit_for_day, days_with_commits, iter_days
from rebuild.models import WalkConfig


FAKE_LOG_LINE = "abc1234def5678|Fix auth bug|Jane Doe|2024-03-15T10:30:00+00:00"


def test_get_commit_for_day_parses_output():
    with patch("rebuild.git_walker._run_git", return_value=FAKE_LOG_LINE):
        commit = get_commit_for_day(Path("/fake/repo"), date(2024, 3, 15))
    assert commit is not None
    assert commit.sha == "abc1234def5678"
    assert commit.message == "Fix auth bug"
    assert commit.author == "Jane Doe"
    assert commit.date == date(2024, 3, 15)


def test_get_commit_for_day_no_output():
    with patch("rebuild.git_walker._run_git", return_value=""):
        commit = get_commit_for_day(Path("/fake/repo"), date(2024, 3, 15))
    assert commit is None


def test_get_commit_for_day_git_error():
    with patch("rebuild.git_walker._run_git", side_effect=subprocess.CalledProcessError(1, "git")):
        commit = get_commit_for_day(Path("/fake/repo"), date(2024, 3, 15))
    assert commit is None


def test_days_with_commits_filters_none():
    config = WalkConfig(
        repo_path=Path("/fake/repo"),
        days=3,
        date_from=date(2024, 3, 13),
        date_to=date(2024, 3, 15),
    )
    side_effects = [None, None, MagicMock()]
    with patch("rebuild.git_walker.get_commit_for_day", side_effect=side_effects):
        results = days_with_commits(config)
    assert len(results) == 1
