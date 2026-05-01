"""Tests for rebuild.tester."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rebuild.models import Endpoint, EndpointStatus, WalkConfig
from rebuild.tester import (
    _fallback_all_timeout,
    _parse_testql_results,
    _run_http_probe,
    _testql_available,
    run_tests,
)


def _ep(path: str = "/api/health", method: str = "GET") -> Endpoint:
    return Endpoint(method=method, path=path, base_url="http://localhost:8003")


# ──────────────────────────────────────────────
# _testql_available
# ──────────────────────────────────────────────

def test_testql_available_missing():
    with patch("rebuild.tester.subprocess.run", side_effect=FileNotFoundError):
        assert _testql_available() is False


def test_testql_available_ok():
    import subprocess
    mock = type("R", (), {"returncode": 0})()
    with patch("rebuild.tester.subprocess.run", return_value=mock):
        assert _testql_available() is True


# ──────────────────────────────────────────────
# _parse_testql_results
# ──────────────────────────────────────────────

def test_parse_testql_results_ok(tmp_path):
    ep = _ep("/api/health")
    results_path = tmp_path / "testql-results.json"
    results_path.write_text(json.dumps([
        {"path": "/api/health", "method": "GET", "passed": True,
         "http_status": 200, "response_time_ms": 42.0, "error": None}
    ]))
    config = WalkConfig(repo_path=tmp_path)
    ep_results = _parse_testql_results(results_path, [ep], config)
    assert len(ep_results) == 1
    assert ep_results[0].status == EndpointStatus.OK
    assert ep_results[0].testql_passed is True
    assert ep_results[0].http_status == 200


def test_parse_testql_results_fail(tmp_path):
    ep = _ep("/api/health")
    results_path = tmp_path / "testql-results.json"
    results_path.write_text(json.dumps([
        {"path": "/api/health", "method": "GET", "passed": False,
         "http_status": 500, "response_time_ms": 10.0, "error": "server error"}
    ]))
    config = WalkConfig(repo_path=tmp_path)
    ep_results = _parse_testql_results(results_path, [ep], config)
    assert ep_results[0].status == EndpointStatus.FAIL
    assert ep_results[0].testql_passed is False


def test_parse_testql_results_missing_endpoint(tmp_path):
    ep = _ep("/api/missing")
    results_path = tmp_path / "testql-results.json"
    results_path.write_text(json.dumps([]))
    config = WalkConfig(repo_path=tmp_path)
    ep_results = _parse_testql_results(results_path, [ep], config)
    assert ep_results[0].status == EndpointStatus.UNKNOWN


# ──────────────────────────────────────────────
# _run_http_probe
# ──────────────────────────────────────────────

def test_run_http_probe_skip_non_get():
    ep = _ep("/api/items", method="POST")
    config = WalkConfig(repo_path=Path("/fake"))
    results = _run_http_probe([ep], config)
    assert results[0].status == EndpointStatus.SKIP


def test_run_http_probe_ok():
    import httpx
    ep = _ep("/api/health")
    config = WalkConfig(repo_path=Path("/fake"))
    mock_response = type("R", (), {"status_code": 200})()
    with patch("rebuild.tester.httpx.get", return_value=mock_response):
        results = _run_http_probe([ep], config)
    assert results[0].status == EndpointStatus.OK
    assert results[0].http_status == 200


def test_run_http_probe_timeout():
    import httpx
    ep = _ep("/api/health")
    config = WalkConfig(repo_path=Path("/fake"))
    with patch("rebuild.tester.httpx.get", side_effect=httpx.TimeoutException("timeout")):
        results = _run_http_probe([ep], config)
    assert results[0].status == EndpointStatus.TIMEOUT


# ──────────────────────────────────────────────
# run_tests — routing
# ──────────────────────────────────────────────

def test_run_tests_uses_http_probe_when_no_testql_dir(tmp_path):
    ep = _ep()
    config = WalkConfig(repo_path=tmp_path, testql_dir=None)
    mock_response = type("R", (), {"status_code": 200})()
    with patch("rebuild.tester.httpx.get", return_value=mock_response):
        results = run_tests([ep], config, tmp_path / "day")
    assert results[0].status == EndpointStatus.OK


def test_fallback_all_timeout():
    eps = [_ep("/a"), _ep("/b")]
    results = _fallback_all_timeout(eps)
    assert all(r.status == EndpointStatus.TIMEOUT for r in results)
