"""Tests for resplit.deployer."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from resplit.deployer import detect_deploy_method
from resplit.models import DeployMethod


def test_detect_docker_compose_yml(tmp_path):
    (tmp_path / "docker-compose.yml").touch()
    assert detect_deploy_method(tmp_path) == DeployMethod.DOCKER_COMPOSE


def test_detect_docker_compose_yaml(tmp_path):
    (tmp_path / "docker-compose.yaml").touch()
    assert detect_deploy_method(tmp_path) == DeployMethod.DOCKER_COMPOSE


def test_detect_uvicorn_server(tmp_path):
    (tmp_path / "server.py").touch()
    assert detect_deploy_method(tmp_path) == DeployMethod.UVICORN


def test_detect_uvicorn_backend_server(tmp_path):
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "server.py").touch()
    assert detect_deploy_method(tmp_path) == DeployMethod.UVICORN


def test_detect_none(tmp_path):
    assert detect_deploy_method(tmp_path) == DeployMethod.NONE
