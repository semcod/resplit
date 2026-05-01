"""Tests for rebuild.application.services.deploy_service."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from rebuild.domain.models import DeployMethod, WalkConfig
from rebuild.application.services.deploy_service import DeployService


def _config(tmp_path: Path, method: DeployMethod = DeployMethod.NONE, dry_run: bool = False, compose_file: str = "docker-compose.yml") -> WalkConfig:
    return WalkConfig(repo_path=tmp_path, deploy_method=method, dry_run=dry_run, compose_file=compose_file)


# ──────────────────────────────────────────────
# start — dry_run
# ──────────────────────────────────────────────

def test_start_dry_run_skips_deploy(tmp_path):
    config = _config(tmp_path, method=DeployMethod.DOCKER_COMPOSE, dry_run=True)
    svc = DeployService(config)
    with patch.object(svc, "_compose_up") as mock_up:
        result = svc.start(tmp_path)
    mock_up.assert_not_called()
    assert result is True


def test_start_none_method_returns_true(tmp_path):
    config = _config(tmp_path, method=DeployMethod.NONE)
    svc = DeployService(config)
    result = svc.start(tmp_path)
    assert result is True


# ──────────────────────────────────────────────
# stop — dry_run
# ──────────────────────────────────────────────

def test_stop_dry_run_skips(tmp_path):
    config = _config(tmp_path, method=DeployMethod.DOCKER_COMPOSE, dry_run=True)
    svc = DeployService(config)
    with patch.object(svc, "_compose_down") as mock_down:
        svc.stop(tmp_path)
    mock_down.assert_not_called()


def test_stop_none_method_skips(tmp_path):
    config = _config(tmp_path, method=DeployMethod.NONE)
    svc = DeployService(config)
    with patch.object(svc, "_compose_down") as mock_down:
        svc.stop(tmp_path)
    mock_down.assert_not_called()


# ──────────────────────────────────────────────
# execute delegates to start
# ──────────────────────────────────────────────

def test_start_none_returns_true(tmp_path):
    config = _config(tmp_path, method=DeployMethod.NONE)
    svc = DeployService(config)
    result = svc.start(tmp_path)
    assert result is True


# ──────────────────────────────────────────────
# docker compose methods
# ──────────────────────────────────────────────

def test_compose_file_finds_yml(tmp_path):
    config = _config(tmp_path)
    svc = DeployService(config)
    (tmp_path / "docker-compose.yml").touch()
    result = svc._compose_file(tmp_path)
    assert result == tmp_path / "docker-compose.yml"


def test_compose_file_finds_yaml(tmp_path):
    config = _config(tmp_path)
    svc = DeployService(config)
    (tmp_path / "docker-compose.yaml").touch()
    result = svc._compose_file(tmp_path)
    assert result == tmp_path / "docker-compose.yaml"


def test_compose_file_explicit(tmp_path):
    config = _config(tmp_path, compose_file="custom-compose.yml")
    svc = DeployService(config)
    (tmp_path / "custom-compose.yml").touch()
    result = svc._compose_file(tmp_path)
    assert result == tmp_path / "custom-compose.yml"
