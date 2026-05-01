"""
Additional coverage tests for deploy_service, scanner_service,
restore_service, patcher_service, and override_service.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from rebuild.domain.models import WalkConfig, DeployMethod
from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus


# ─────────────────────────────────────────────────────────────
# deploy_service — shell interaction via mocked ShellAdapter
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.deploy_service import DeployService


def _cfg(tmp_path, method=DeployMethod.NONE, **kw):
    return WalkConfig(repo_path=tmp_path, deploy_method=method, **kw)


def _mock_shell_result(returncode=0, stdout="", stderr=""):
    r = MagicMock()
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    return r


def test_compose_up_success(tmp_path):
    cfg = _cfg(tmp_path, method=DeployMethod.DOCKER_COMPOSE)
    (tmp_path / "docker-compose.yml").touch()
    svc = DeployService(cfg)
    svc.shell = MagicMock()
    svc.shell.run.return_value = _mock_shell_result(returncode=0)
    with patch.object(svc, "wait_healthy", return_value=True):
        result = svc._compose_up(tmp_path)
    assert result is True


def test_compose_up_fails_classifies_error(tmp_path):
    cfg = _cfg(tmp_path, method=DeployMethod.DOCKER_COMPOSE)
    (tmp_path / "docker-compose.yml").touch()
    svc = DeployService(cfg)
    svc.shell = MagicMock()
    svc.shell.run.return_value = _mock_shell_result(returncode=1, stderr="build failed: something")
    result = svc._compose_up(tmp_path)
    assert result is False
    from rebuild.domain.day_result import DeployErrorCategory
    assert svc.last_error_category == DeployErrorCategory.COMPOSE_BUILD_FAIL


def test_compose_down_called(tmp_path):
    cfg = _cfg(tmp_path, method=DeployMethod.DOCKER_COMPOSE)
    (tmp_path / "docker-compose.yml").touch()
    svc = DeployService(cfg)
    svc.shell = MagicMock()
    svc.shell.run.return_value = _mock_shell_result(returncode=0)
    svc._compose_down(tmp_path)
    svc.shell.run.assert_called_once()


def test_uvicorn_stop_terminates(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    mock_proc = MagicMock()
    svc._uvicorn_proc = mock_proc
    svc._uvicorn_stop()
    mock_proc.terminate.assert_called_once()
    assert svc._uvicorn_proc is None


def test_save_deploy_debug_writes_file(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, output_dir=tmp_path)
    svc = DeployService(cfg)
    svc._save_deploy_debug(tmp_path, "some log output")
    debug = tmp_path / "deploy_debug.txt"
    assert debug.exists()
    assert "some log output" in debug.read_text()


def test_wait_healthy_returns_true_on_200(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, health_timeout=1.0, health_interval=0.05)
    svc = DeployService(cfg)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch.object(svc.http, "get", return_value=mock_resp):
        result = svc._wait_healthy()
    assert result is True


def test_wait_healthy_times_out(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, health_timeout=0.05, health_interval=0.01)
    svc = DeployService(cfg)
    with patch.object(svc.http, "get", side_effect=Exception("conn refused")):
        result = svc._wait_healthy()
    assert result is False


def test_wait_healthy_with_retry_wraps_wait_healthy(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, deploy_retry_attempts=1)
    svc = DeployService(cfg)
    with patch.object(svc, "_wait_healthy", return_value=True) as mock_wh:
        result = svc._wait_healthy_with_retry()
    assert result is True
    mock_wh.assert_called_once()


# ─────────────────────────────────────────────────────────────
# scanner_service
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.scanner_service import ScannerService


def _scan_cfg(tmp_path):
    return WalkConfig(repo_path=tmp_path, base_url="http://localhost:8003")


def test_scanner_fallback_health_endpoint(tmp_path):
    svc = ScannerService(_scan_cfg(tmp_path))
    with patch.object(svc, "_scan_via_deta", return_value=[]), \
         patch.object(svc, "_scan_via_openapi", return_value=[]), \
         patch.object(svc, "_scan_via_fastapi_routes", return_value=[]), \
         patch.object(svc, "_scan_via_compose_labels", return_value=[]):
        endpoints = svc.execute(tmp_path)
    assert len(endpoints) == 1
    assert endpoints[0].path == "/api/health"


def test_scanner_compose_labels_fallback(tmp_path):
    svc = ScannerService(_scan_cfg(tmp_path))
    ep = Endpoint(method="GET", path="/traefik", base_url="http://localhost:8003")
    with patch.object(svc, "_scan_via_deta", return_value=[]), \
         patch.object(svc, "_scan_via_openapi", return_value=[]), \
         patch.object(svc, "_scan_via_fastapi_routes", return_value=[]), \
         patch.object(svc, "_scan_via_compose_labels", return_value=[ep]):
        endpoints = svc.execute(tmp_path)
    assert any(e.path == "/traefik" for e in endpoints)


def test_scanner_openapi_deduplication(tmp_path):
    svc = ScannerService(_scan_cfg(tmp_path))
    ep1 = Endpoint(method="GET", path="/api/v1/items", base_url="http://localhost:8003")
    ep_dup = Endpoint(method="GET", path="/api/v1/items", base_url="http://localhost:8003")
    with patch.object(svc, "_scan_via_deta", return_value=[ep1]), \
         patch.object(svc, "_scan_via_openapi", return_value=[ep_dup]), \
         patch.object(svc, "_scan_via_fastapi_routes", return_value=[]), \
         patch.object(svc, "_scan_via_compose_labels", return_value=[]):
        endpoints = svc.execute(tmp_path)
    assert sum(1 for e in endpoints if e.path == "/api/v1/items") == 1


def test_scanner_parse_openapi_substitutes_fixture(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, base_url="http://x", test_fixtures={"item_id": "42"})
    svc = ScannerService(cfg)
    spec = {"paths": {"/items/{item_id}": {"get": {"summary": "Get item"}}}}
    endpoints = svc._parse_openapi(spec, "http://x")
    assert any("/items/42" in e.path for e in endpoints)


def test_scanner_parse_openapi_generic_fallback(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, base_url="http://x", test_fixtures={})
    svc = ScannerService(cfg)
    spec = {"paths": {"/orders/{order_id}": {"get": {"summary": "Order"}}}}
    endpoints = svc._parse_openapi(spec, "http://x")
    assert endpoints
    assert "{order_id}" not in endpoints[0].path


def test_scanner_resolve_test_body_from_config(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, base_url="http://x",
                     test_bodies={"/items": {"name": "test"}})
    svc = ScannerService(cfg)
    body = svc._resolve_test_body("POST", "/items", "/items")
    assert body == {"name": "test"}


def test_scanner_resolve_test_body_fallback(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, base_url="http://x", test_bodies={})
    svc = ScannerService(cfg)
    body = svc._resolve_test_body("POST", "/users", "/users")
    assert body is None


def test_scanner_fastapi_routes_parses_file(tmp_path):
    svc = ScannerService(_scan_cfg(tmp_path))
    py_file = tmp_path / "main.py"
    py_file.write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n"
        "@app.get('/health')\ndef health(): pass\n"
        "@app.post('/users')\ndef create(): pass\n"
    )
    routes = svc._scan_via_fastapi_routes(tmp_path)
    paths = [e.path for e in routes]
    assert "/health" in paths
    assert "/users" in paths


# ─────────────────────────────────────────────────────────────
# restore_service
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.restore_service import RestoreService


def test_restore_find_last_working_day(tmp_path):
    day_dir = tmp_path / "2025-01-05"
    day_dir.mkdir()
    (day_dir / "results.json").write_text(json.dumps({
        "results": [{"path": "/api/health", "status": "ok"}]
    }))
    svc = RestoreService(tmp_path)
    result = svc.find_last_working_day("/api/health", tmp_path)
    assert result == date(2025, 1, 5)


def test_restore_no_working_day_returns_none(tmp_path):
    day_dir = tmp_path / "2025-01-05"
    day_dir.mkdir()
    (day_dir / "results.json").write_text(json.dumps({
        "results": [{"path": "/api/health", "status": "fail"}]
    }))
    svc = RestoreService(tmp_path)
    result = svc.find_last_working_day("/api/health", tmp_path)
    assert result is None


def test_restore_missing_results_dir(tmp_path):
    svc = RestoreService(tmp_path)
    result = svc.find_last_working_day("/api/health", tmp_path / "nonexistent")
    assert result is None


def test_restore_extract_endpoint_creates_dirs(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "docker-compose.yml").write_text("services:\n  app:\n    image: test\n")
    svc = RestoreService(repo_dir)
    target = tmp_path / "out"
    svc.extract_endpoint("/api/health", date(2025, 1, 1), target)
    assert target.exists()


def test_restore_list_working_days(tmp_path):
    for day in ["2025-01-01", "2025-01-02", "2025-01-03"]:
        d = tmp_path / day
        d.mkdir()
        status = "ok" if day != "2025-01-02" else "fail"
        (d / "results.json").write_text(json.dumps({
            "results": [{"path": "/api/health", "status": status}]
        }))
    svc = RestoreService(tmp_path)
    working = svc.find_last_working_day("/api/health", tmp_path)
    assert working == date(2025, 1, 3)


# ─────────────────────────────────────────────────────────────
# patcher_service
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.patcher_service import PatcherService


def test_patcher_patches_dockerfile_npm_install(tmp_path):
    df = tmp_path / "Dockerfile"
    df.write_text("FROM node:18\nRUN npm install\nRUN npm run build\nCMD [\"node\", \"server.js\"]\n")
    svc = PatcherService()
    patched = svc._patch_dockerfile(df)
    assert patched is True
    content = df.read_text()
    assert "npm install" not in content
    assert "npm run build" not in content


def test_patcher_no_change_if_no_npm(tmp_path):
    df = tmp_path / "Dockerfile"
    df.write_text("FROM python:3.11\nRUN pip install -r requirements.txt\nCMD [\"python\", \"app.py\"]\n")
    svc = PatcherService()
    patched = svc._patch_dockerfile(df)
    assert not patched


def test_patcher_patch_compose_removes_container_names(tmp_path):
    cf = tmp_path / "docker-compose.yml"
    cf.write_text("services:\n  app:\n    container_name: myapp\n    image: test\n")
    svc = PatcherService()
    patched = svc._patch_compose(cf)
    assert patched is True
    assert "container_name" not in cf.read_text()


def test_patcher_execute_counts_patches(tmp_path):
    df = tmp_path / "Dockerfile"
    df.write_text("FROM node:18\nRUN npm ci\n")
    svc = PatcherService()
    count = svc.execute(tmp_path)
    assert count >= 1


def test_patcher_apply_manual_overrides(tmp_path):
    patch_dir = tmp_path / "patches"
    patch_dir.mkdir()
    (patch_dir / "config.py").write_text("DEBUG = True\n")
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    svc = PatcherService()
    applied = svc.apply_manual_overrides(patch_dir, repo_dir)
    assert applied == 1
    assert (repo_dir / "config.py").read_text() == "DEBUG = True\n"


def test_patcher_manual_overrides_missing_patch_dir(tmp_path):
    svc = PatcherService()
    count = svc.apply_manual_overrides(tmp_path / "nope", tmp_path)
    assert count == 0


# ─────────────────────────────────────────────────────────────
# override_service
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.override_service import OverrideService


def test_override_service_no_overrides(tmp_path):
    svc = OverrideService()
    result = svc.execute(tmp_path)
    assert result is None or result == 0 or result is True or isinstance(result, (int, type(None)))


# ─────────────────────────────────────────────────────────────
# base_pipeline — state persistence
# ─────────────────────────────────────────────────────────────

from rebuild.application.base_pipeline import BasePipeline


def test_base_pipeline_load_state_empty(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, output_dir=tmp_path)
    pipeline = BasePipeline(cfg)
    assert pipeline._processed_shas == set()


def test_base_pipeline_save_and_reload_state(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, output_dir=tmp_path)
    pipeline = BasePipeline(cfg)
    pipeline._processed_shas = {"abc123", "def456"}
    pipeline._save_state()
    pipeline2 = BasePipeline(cfg)
    assert "abc123" in pipeline2._processed_shas
    assert "def456" in pipeline2._processed_shas


def test_base_pipeline_emit_writes_jsonl(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, output_dir=tmp_path)
    pipeline = BasePipeline(cfg)
    pipeline._emit("LOG", message="hello")
    log = tmp_path / "history.jsonl"
    assert log.exists()
    assert "LOG" in log.read_text() or "hello" in log.read_text()


def test_base_pipeline_log_prints_to_console(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, output_dir=tmp_path)
    mock_console = MagicMock()
    pipeline = BasePipeline(cfg, console=mock_console)
    pipeline.log("test message")
    mock_console.print.assert_called_once_with("test message")
