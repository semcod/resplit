"""Tests for rebuild.application.services.scanner_service."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rebuild.domain.models import WalkConfig
from rebuild.domain.endpoint import Endpoint
from rebuild.application.services.scanner_service import ScannerService


def _config(tmp_path: Path, base_url: str = "http://localhost:8003") -> WalkConfig:
    return WalkConfig(repo_path=tmp_path, base_url=base_url)


# ──────────────────────────────────────────────
# _parse_openapi
# ──────────────────────────────────────────────

def test_parse_openapi_returns_endpoints(tmp_path):
    config = _config(tmp_path)
    service = ScannerService(config)
    spec = {
        "paths": {
            "/api/health": {"get": {"summary": "Health check"}},
            "/api/items": {"post": {"summary": "Create item"}, "get": {"summary": "List items"}},
        }
    }
    endpoints = service._parse_openapi(spec, config.base_url)
    methods = {(e.method, e.path) for e in endpoints}
    assert ("GET", "/api/health") in methods
    assert ("POST", "/api/items") in methods
    assert ("GET", "/api/items") in methods


def test_parse_openapi_ignores_unknown_methods(tmp_path):
    config = _config(tmp_path)
    service = ScannerService(config)
    spec = {"paths": {"/api/ws": {"connect": {"summary": "WebSocket"}}}}
    endpoints = service._parse_openapi(spec, config.base_url)
    assert endpoints == []


def test_parse_openapi_empty_paths(tmp_path):
    config = _config(tmp_path)
    service = ScannerService(config)
    endpoints = service._parse_openapi({"paths": {}}, config.base_url)
    assert endpoints == []


# ──────────────────────────────────────────────
# _scan_via_compose_labels
# ──────────────────────────────────────────────

def test_scan_via_compose_labels_finds_traefik_prefix(tmp_path):
    compose = tmp_path / "docker-compose.yml"
    compose.write_text("""
services:
  backend:
    image: myapp
    labels:
      - "traefik.http.routers.backend.rule=PathPrefix(`/api`)"
""")
    config = _config(tmp_path)
    service = ScannerService(config)
    endpoints = service._scan_via_compose_labels(tmp_path)
    assert len(endpoints) == 1
    assert endpoints[0].path == "/api"
    assert endpoints[0].service == "backend"


def test_scan_via_compose_labels_no_compose_file(tmp_path):
    config = _config(tmp_path)
    service = ScannerService(config)
    endpoints = service._scan_via_compose_labels(tmp_path)
    assert endpoints == []


def test_scan_via_compose_labels_dict_labels(tmp_path):
    compose = tmp_path / "docker-compose.yml"
    compose.write_text("""
services:
  api:
    image: api
    labels:
      traefik.rule: "PathPrefix(`/v1`)"
""")
    config = _config(tmp_path)
    service = ScannerService(config)
    endpoints = service._scan_via_compose_labels(tmp_path)
    assert any(e.path == "/v1" for e in endpoints)


# ──────────────────────────────────────────────
# _ports_to_endpoints
# ──────────────────────────────────────────────

def test_ports_to_endpoints(tmp_path):
    config = _config(tmp_path)
    service = ScannerService(config)
    data = {
        "services": [
            {"name": "backend", "ports": [{"host_port": 8080}]}
        ]
    }
    endpoints = service._ports_to_endpoints(data, "http://localhost:8003")
    paths = [e.path for e in endpoints]
    assert "/api/health" in paths
    assert "/health" in paths
    assert all(e.service == "backend" for e in endpoints)


def test_ports_to_endpoints_no_services(tmp_path):
    config = _config(tmp_path)
    service = ScannerService(config)
    endpoints = service._ports_to_endpoints({"services": []}, "http://localhost:8003")
    assert endpoints == []


# ──────────────────────────────────────────────
# execute — fallback chain
# ──────────────────────────────────────────────

def test_execute_falls_back_to_health(tmp_path):
    config = _config(tmp_path)
    service = ScannerService(config)
    with patch.object(service, "_scan_via_deta", return_value=[]), \
         patch.object(service, "_scan_via_openapi", return_value=[]), \
         patch.object(service, "_scan_via_compose_labels", return_value=[]):
        endpoints = service.execute(tmp_path)
    assert len(endpoints) == 1
    assert endpoints[0].path == "/api/health"


def test_execute_deta_takes_priority(tmp_path):
    config = _config(tmp_path)
    service = ScannerService(config)
    deta_ep = [Endpoint(method="GET", path="/deta", base_url="http://localhost:8003")]
    openapi_ep = [Endpoint(method="GET", path="/openapi", base_url="http://localhost:8003")]
    with patch.object(service, "_scan_via_deta", return_value=deta_ep), \
         patch.object(service, "_scan_via_openapi", return_value=openapi_ep):
        endpoints = service.execute(tmp_path)
    paths = [e.path for e in endpoints]
    assert "/deta" in paths
    assert "/openapi" in paths


def test_execute_deduplicates_openapi_vs_deta(tmp_path):
    config = _config(tmp_path)
    service = ScannerService(config)
    ep = Endpoint(method="GET", path="/api/health", base_url="http://localhost:8003")
    with patch.object(service, "_scan_via_deta", return_value=[ep]), \
         patch.object(service, "_scan_via_openapi", return_value=[ep]):
        endpoints = service.execute(tmp_path)
    assert len([e for e in endpoints if e.path == "/api/health"]) == 1
