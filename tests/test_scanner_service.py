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


# ──────────────────────────────────────────────
# Diff-aware caching (Sprint 3 / 2026-05-07)
# ──────────────────────────────────────────────

_FASTAPI_SAMPLE = '''\
from fastapi import APIRouter, FastAPI

router = APIRouter(prefix="/api")

@router.get("/health")
def health():
    return {"ok": True}

@router.post("/items")
def create_item():
    return {}
'''


def _make_py(tmp_path: Path, name: str, source: str) -> Path:
    p = tmp_path / name
    p.write_text(source, encoding="utf-8")
    return p


def test_cache_starts_empty(tmp_path):
    service = ScannerService(_config(tmp_path))
    assert service.cache_stats == {"hits": 0, "misses": 0, "size": 0}


def test_cache_miss_then_hit_for_same_content(tmp_path):
    py_file = _make_py(tmp_path, "routes.py", _FASTAPI_SAMPLE)
    service = ScannerService(_config(tmp_path))

    eps1 = service._endpoints_for_python_file(py_file)
    assert {(e.method, e.path) for e in eps1} == {("GET", "/api/health"), ("POST", "/api/items")}
    assert service.cache_stats == {"hits": 0, "misses": 1, "size": 1}

    eps2 = service._endpoints_for_python_file(py_file)
    assert eps2 == eps1
    assert service.cache_stats == {"hits": 1, "misses": 1, "size": 1}


def test_cache_hits_across_files_with_identical_content(tmp_path):
    a = _make_py(tmp_path, "a.py", _FASTAPI_SAMPLE)
    b = _make_py(tmp_path, "b.py", _FASTAPI_SAMPLE)   # byte-identical → same hash
    service = ScannerService(_config(tmp_path))

    service._endpoints_for_python_file(a)
    service._endpoints_for_python_file(b)
    stats = service.cache_stats
    assert stats["misses"] == 1
    assert stats["hits"] == 1
    assert stats["size"] == 1


def test_cache_miss_when_content_changes(tmp_path):
    py_file = _make_py(tmp_path, "routes.py", _FASTAPI_SAMPLE)
    service = ScannerService(_config(tmp_path))
    service._endpoints_for_python_file(py_file)

    # Modify content → new hash → fresh parse
    py_file.write_text(_FASTAPI_SAMPLE + "\n# changed\n", encoding="utf-8")
    service._endpoints_for_python_file(py_file)
    stats = service.cache_stats
    assert stats["misses"] == 2
    assert stats["hits"] == 0
    assert stats["size"] == 2


def test_reset_cache_clears_state(tmp_path):
    py_file = _make_py(tmp_path, "routes.py", _FASTAPI_SAMPLE)
    service = ScannerService(_config(tmp_path))
    service._endpoints_for_python_file(py_file)
    assert service.cache_stats["size"] == 1

    service.reset_cache()
    assert service.cache_stats == {"hits": 0, "misses": 0, "size": 0}


def test_cache_isolates_callers_from_mutation(tmp_path):
    py_file = _make_py(tmp_path, "routes.py", _FASTAPI_SAMPLE)
    service = ScannerService(_config(tmp_path))

    eps1 = service._endpoints_for_python_file(py_file)
    eps1.clear()   # caller mutates returned list → must not affect cache

    eps2 = service._endpoints_for_python_file(py_file)
    assert len(eps2) == 2
    assert service.cache_stats["hits"] == 1


def test_cache_caches_unparseable_files_as_empty(tmp_path):
    bad = _make_py(tmp_path, "bad.py", "def broken(:\n")  # SyntaxError
    service = ScannerService(_config(tmp_path))

    assert service._endpoints_for_python_file(bad) == []
    # Second call must hit the cache, not re-parse.
    assert service._endpoints_for_python_file(bad) == []
    stats = service.cache_stats
    assert stats["misses"] == 1
    assert stats["hits"] == 1


def test_scan_via_fastapi_routes_uses_cache(tmp_path):
    _make_py(tmp_path, "routes_a.py", _FASTAPI_SAMPLE)
    _make_py(tmp_path, "routes_b.py", _FASTAPI_SAMPLE)   # identical → cache hit
    service = ScannerService(_config(tmp_path))

    endpoints = service._scan_via_fastapi_routes(tmp_path)
    paths = {(e.method, e.path) for e in endpoints}
    assert ("GET", "/api/health") in paths
    assert ("POST", "/api/items") in paths

    stats = service.cache_stats
    assert stats["misses"] == 1
    assert stats["hits"] == 1
