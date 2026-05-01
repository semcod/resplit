"""Tests for rebuild.endpoint_scanner."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.endpoint_scanner import (
    _parse_openapi,
    _ports_to_endpoints,
    _scan_via_compose_labels,
    scan_endpoints,
)
from rebuild.models import WalkConfig


OPENAPI_SPEC = {
    "paths": {
        "/api/health": {"get": {"summary": "Health check"}},
        "/api/items": {
            "get": {"summary": "List items"},
            "post": {"summary": "Create item"},
        },
    }
}


def test_parse_openapi():
    endpoints = _parse_openapi(OPENAPI_SPEC, "http://localhost:8003")
    assert len(endpoints) == 3
    paths = [(e.method, e.path) for e in endpoints]
    assert ("GET", "/api/health") in paths
    assert ("GET", "/api/items") in paths
    assert ("POST", "/api/items") in paths


def test_ports_to_endpoints():
    data = {
        "services": [
            {"name": "backend", "ports": [{"host_port": 8003}]},
        ]
    }
    endpoints = _ports_to_endpoints(data, "http://localhost:8003")
    assert len(endpoints) == 3
    assert all(e.service == "backend" for e in endpoints)


def test_scan_via_compose_labels(tmp_path):
    compose = tmp_path / "docker-compose.yml"
    compose.write_text("""
services:
  backend:
    labels:
      - "traefik.http.routers.backend.rule=PathPrefix(`/api`)"
""")
    config = WalkConfig(repo_path=tmp_path)
    endpoints = _scan_via_compose_labels(tmp_path, config)
    assert len(endpoints) == 1
    assert endpoints[0].path == "/api"
    assert endpoints[0].service == "backend"


def test_scan_endpoints_minimal_fallback(tmp_path):
    config = WalkConfig(repo_path=tmp_path)
    with patch("rebuild.endpoint_scanner._scan_via_deta", return_value=[]), \
         patch("rebuild.endpoint_scanner._scan_via_openapi", return_value=[]), \
         patch("rebuild.endpoint_scanner._scan_via_compose_labels", return_value=[]):
        endpoints = scan_endpoints(tmp_path, config)
    assert len(endpoints) == 1
    assert endpoints[0].path == "/api/health"
