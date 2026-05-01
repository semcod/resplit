"""
Smoke tests for interface modules — imports, class instantiation,
and pure-logic helpers that don't require live CLI/TUI.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from rebuild.domain.models import WalkConfig, DeployMethod
from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from rebuild.domain.day_result import DayResult
from rebuild.domain.commit import CommitInfo


# ─────────────────────────────────────────────────────────────
# interfaces/commands/helpers.py
# ─────────────────────────────────────────────────────────────

from rebuild.interfaces.commands.helpers import (
    print_summary_table, serve_reports
)
from rebuild.infrastructure.config_loader import ConfigLoader


def test_print_summary_table_empty():
    console = MagicMock()
    print_summary_table([], console)
    console.print.assert_called()


def test_config_loader_roundtrip(tmp_path):
    f = tmp_path / "rebuild.yaml"
    f.write_text("project:\n  days: 5\n")
    data = ConfigLoader.load(f)
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, data)
    assert cfg.days == 5


# ─────────────────────────────────────────────────────────────
# interfaces/dashboard.py — pure data helpers
# ─────────────────────────────────────────────────────────────

from rebuild.interfaces.dashboard import generate_dashboard, _render_html as _dash_render_html


def test_generate_dashboard_empty(tmp_path):
    result = generate_dashboard([], tmp_path)
    assert result is not None


def test_dashboard_render_html_no_data():
    html = _dash_render_html([], [], [], 0)
    assert isinstance(html, str)
    assert "<html" in html or "<!DOCTYPE" in html or "html" in html.lower()


# ─────────────────────────────────────────────────────────────
# interfaces/evolution_viz.py
# ─────────────────────────────────────────────────────────────

from rebuild.interfaces.evolution_viz import _render_html as _evo_render_html


def test_evolution_render_html_empty():
    result = _evo_render_html([], "/repo", "Test Evolution")
    assert isinstance(result, str)
    assert "Evolution" in result or "html" in result.lower()


# ─────────────────────────────────────────────────────────────
# tui/compat.py
# ─────────────────────────────────────────────────────────────

from rebuild.interfaces.tui.compat import TEXTUAL_OK


def test_textual_ok_is_bool():
    assert isinstance(TEXTUAL_OK, bool)


# ─────────────────────────────────────────────────────────────
# deploy_service — more branch coverage
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.deploy_service import DeployService


def _cfg(tmp_path, method=DeployMethod.NONE, **kw):
    return WalkConfig(repo_path=tmp_path, deploy_method=method, **kw)


def test_start_replay_checks_health(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, deploy_method=DeployMethod.DOCKER_COMPOSE, replay=True)
    svc = DeployService(cfg)
    with patch.object(svc, "_wait_healthy_with_retry", return_value=True) as mock:
        result = svc.start(tmp_path)
    assert result is True
    mock.assert_called_once()


def test_stop_replay_skips_down(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, deploy_method=DeployMethod.DOCKER_COMPOSE, replay=True)
    svc = DeployService(cfg)
    with patch.object(svc, "_compose_down") as mock_down:
        svc.stop(tmp_path)
    mock_down.assert_not_called()


def test_compose_file_raises_when_missing(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    with pytest.raises(FileNotFoundError):
        svc._compose_file(tmp_path)


def test_run_with_retry_success_on_second_attempt(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, deploy_retry_attempts=3, deploy_retry_backoff_seconds=0.0)
    svc = DeployService(cfg)
    attempts = []
    def action():
        attempts.append(1)
        return len(attempts) >= 2
    result = svc._run_with_retry(action, "deploy")
    assert result is True
    assert len(attempts) == 2


def test_classify_error_alembic(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    from rebuild.domain.day_result import DeployErrorCategory
    assert svc._classify_deploy_error("alembic upgrade head failed") == DeployErrorCategory.MIGRATION_FAIL


def test_classify_error_keyerror(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    from rebuild.domain.day_result import DeployErrorCategory
    assert svc._classify_deploy_error("KeyError: 'SECRET_KEY'") == DeployErrorCategory.MISSING_ENV


def test_classify_error_dockerfile(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    from rebuild.domain.day_result import DeployErrorCategory
    assert svc._classify_deploy_error("Dockerfile not found") == DeployErrorCategory.COMPOSE_BUILD_FAIL
