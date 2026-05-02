"""Coverage tests for rebuild/interfaces/cli.py using typer CliRunner."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rebuild.interfaces.cli import app

runner = CliRunner()


# ─────────────────────────────────────────────
# version
# ─────────────────────────────────────────────

def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "rebuild" in result.output


# ─────────────────────────────────────────────
# init
# ─────────────────────────────────────────────

def test_init_creates_files(tmp_path):
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / ".env").exists()


def test_init_force_overwrites(tmp_path):
    (tmp_path / "rebuild.yaml").write_text("old")
    result = runner.invoke(app, ["init", str(tmp_path), "--force"])
    assert result.exit_code == 0


def test_init_no_overwrite_existing(tmp_path):
    (tmp_path / "rebuild.yaml").write_text("existing")
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "rebuild.yaml").read_text() == "existing"


# ─────────────────────────────────────────────
# report
# ─────────────────────────────────────────────

def test_report_no_results(tmp_path):
    with patch("rebuild.interfaces.cli.HistoryService") as MockHist:
        MockHist.return_value.execute.return_value = []
        result = runner.invoke(app, ["report", "--results-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Brak" in result.output


def test_report_with_results(tmp_path):
    from rebuild.domain.day_result import DayResult
    from rebuild.domain.models import DeployMethod
    from datetime import date
    fake = DayResult(day=date(2025, 1, 1), commit=None, deploy_method=DeployMethod.NONE,
                     deploy_success=True, endpoints=[], endpoint_results=[],
                     output_dir=tmp_path / "2025-01-01")
    (tmp_path / "2025-01-01").mkdir()
    with patch("rebuild.interfaces.cli.HistoryService") as MockHist, \
         patch("rebuild.interfaces.cli.ReporterService") as MockReporter:
        MockHist.return_value.execute.return_value = [fake]
        MockReporter.return_value.save_timeline_index.return_value = None
        result = runner.invoke(app, ["report", "--results-dir", str(tmp_path)])
    assert result.exit_code == 0


# ─────────────────────────────────────────────
# dashboard
# ─────────────────────────────────────────────

def test_dashboard_no_results(tmp_path):
    with patch("rebuild.interfaces.cli.HistoryService") as MockHist:
        MockHist.return_value.execute.return_value = []
        result = runner.invoke(app, ["dashboard", "--results-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Brak" in result.output


def test_dashboard_with_results(tmp_path):
    from rebuild.domain.day_result import DayResult
    from rebuild.domain.models import DeployMethod
    from datetime import date
    fake = DayResult(day=date(2025, 1, 1), commit=None, deploy_method=DeployMethod.NONE,
                     deploy_success=True, endpoints=[], endpoint_results=[],
                     output_dir=tmp_path / "2025-01-01")
    with patch("rebuild.interfaces.cli.HistoryService") as MockHist, \
         patch("rebuild.interfaces.cli.generate_dashboard", return_value=tmp_path / "dashboard.html", create=True):
        MockHist.return_value.execute.return_value = [fake]
        result = runner.invoke(app, ["dashboard", "--results-dir", str(tmp_path)])


# ─────────────────────────────────────────────
# serve
# ─────────────────────────────────────────────

def test_serve_missing_dir(tmp_path):
    result = runner.invoke(app, ["serve", "--results-dir", str(tmp_path / "nonexistent")])
    assert result.exit_code != 0


# ─────────────────────────────────────────────
# walk (dry-run with no git repo exits gracefully)
# ─────────────────────────────────────────────

def test_walk_no_git_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    result = runner.invoke(app, ["walk", str(repo), "--dry-run", "--deploy", "none", "--days", "1"])
    assert result.exit_code != 0


def test_walk_dry_run_no_results(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    with patch("rebuild.interfaces.commands.walk_command.Pipeline") as MockPipeline:
        MockPipeline.return_value.run.return_value = []
        result = runner.invoke(app, ["walk", str(repo), "--dry-run", "--deploy", "none", "--days", "1"])
    assert "Brak" in result.output or result.exit_code == 0


# ─────────────────────────────────────────────
# restore
# ─────────────────────────────────────────────

def test_restore_not_found(tmp_path):
    with patch("rebuild.interfaces.cli.RestoreService") as MockRestore:
        MockRestore.return_value.find_last_working_day.return_value = None
        result = runner.invoke(app, [
            "restore", "/api/health", str(tmp_path),
            "--results-dir", str(tmp_path)
        ])
    assert result.exit_code != 0
    assert "Nie znaleziono" in result.output


def test_restore_success(tmp_path):
    from datetime import date
    with patch("rebuild.interfaces.cli.RestoreService") as MockRestore:
        MockRestore.return_value.find_last_working_day.return_value = date(2025, 1, 1)
        MockRestore.return_value.extract_endpoint.return_value = None
        result = runner.invoke(app, [
            "restore", "/api/health", str(tmp_path),
            "--results-dir", str(tmp_path)
        ])
    assert result.exit_code == 0
    assert "2025-01-01" in result.output


# ─────────────────────────────────────────────
# auto_pr
# ─────────────────────────────────────────────

def test_auto_pr_missing_file(tmp_path):
    result = runner.invoke(app, [
        "auto-pr", str(tmp_path / "analysis.json")
    ])
    assert result.exit_code != 0
    assert "nie" in result.output


def test_auto_pr_invalid_json(tmp_path):
    f = tmp_path / "analysis.json"
    f.write_text("{invalid json")
    result = runner.invoke(app, ["auto-pr", str(f)])
    assert result.exit_code != 0


def test_auto_pr_no_config(tmp_path):
    f = tmp_path / "analysis.json"
    f.write_text('{"other": "data"}')
    import rebuild.application.services.pr_service as pr_mod
    with patch.object(pr_mod, "load_config_from_env", return_value=None):
        result = runner.invoke(app, ["auto-pr", str(f)])
    assert result.exit_code != 0


def test_auto_pr_unknown_format(tmp_path):
    f = tmp_path / "analysis.json"
    f.write_text('{"other": "data"}')
    import rebuild.application.services.pr_service as pr_mod
    with patch.object(pr_mod, "load_config_from_env", return_value=MagicMock()):
        result = runner.invoke(app, ["auto-pr", str(f)])
    assert "Nieznany format" in result.output or result.exit_code != 0
