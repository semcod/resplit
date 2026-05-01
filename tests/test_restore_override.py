"""
Coverage tests for restore_service and override_service deeper paths.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from rebuild.application.services.restore_service import RestoreService
from rebuild.application.services.override_service import OverrideService


# ─────────────────────────────────────────────────────────────
# RestoreService — deeper paths
# ─────────────────────────────────────────────────────────────

def test_find_backend_files_returns_matching(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    py_file = repo / "api" / "health.py"
    py_file.parent.mkdir()
    py_file.write_text("@router.get('/api/health')\ndef health(): pass\n")
    svc = RestoreService(repo)
    files = svc._find_backend_files("/api/health")
    assert any(f.name == "health.py" for f in files)


def test_find_backend_files_skips_venv(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    venv_file = repo / ".venv" / "lib" / "site.py"
    venv_file.parent.mkdir(parents=True)
    venv_file.write_text("/api/health route here\n")
    svc = RestoreService(repo)
    files = svc._find_backend_files("/api/health")
    assert not any(".venv" in str(f) for f in files)


def test_is_page_endpoint_api(tmp_path):
    svc = RestoreService(tmp_path)
    assert not svc._is_page_endpoint("/api/users")


def test_is_page_endpoint_page(tmp_path):
    svc = RestoreService(tmp_path)
    assert svc._is_page_endpoint("/dashboard")


def test_write_readme(tmp_path):
    svc = RestoreService(tmp_path)
    target = tmp_path / "out"
    target.mkdir()
    svc._write_readme(target, "/api/health", date(2025, 1, 5), [])
    readme = target / "README.md"
    assert readme.exists()
    content = readme.read_text()
    assert "/api/health" in content
    assert "2025-01-05" in content


def test_write_readme_with_files(tmp_path):
    svc = RestoreService(tmp_path)
    target = tmp_path / "out"
    target.mkdir()
    fake_files = [tmp_path / f"handler{i}.py" for i in range(3)]
    svc._write_readme(target, "/api/orders", date(2025, 2, 1), fake_files)
    content = (target / "README.md").read_text()
    assert "handler0.py" in content


def test_extract_endpoint_copies_compose(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "docker-compose.yml").write_text("services:\n  app:\n    image: test\n")
    svc = RestoreService(repo)
    target = tmp_path / "out"
    svc.extract_endpoint("/api/health", date(2025, 1, 1), target)
    assert (target / "docker" / "docker-compose.yml").exists()


def test_extract_endpoint_copies_backend_dockerfile(tmp_path):
    repo = tmp_path / "repo"
    (repo / "backend").mkdir(parents=True)
    (repo / "backend" / "Dockerfile").write_text("FROM python:3.11\n")
    svc = RestoreService(repo)
    target = tmp_path / "out"
    svc.extract_endpoint("/api/health", date(2025, 1, 1), target)
    assert (target / "docker" / "Dockerfile.backend").exists()


def test_find_last_working_old_schema(tmp_path):
    day_dir = tmp_path / "2025-03-15"
    day_dir.mkdir()
    (day_dir / "results.json").write_text(json.dumps([
        {"path": "/api/health", "status": "ok"},
    ]))
    svc = RestoreService(tmp_path)
    result = svc.find_last_working_day("/api/health", tmp_path)
    assert result == date(2025, 3, 15)


def test_find_last_working_skips_invalid_day_dirs(tmp_path):
    (tmp_path / "not-a-date").mkdir()
    (tmp_path / "2025-01-10").mkdir()
    (tmp_path / "2025-01-10" / "results.json").write_text(json.dumps({
        "results": [{"path": "/api/health", "status": "ok"}]
    }))
    svc = RestoreService(tmp_path)
    result = svc.find_last_working_day("/api/health", tmp_path)
    assert result == date(2025, 1, 10)


# ─────────────────────────────────────────────────────────────
# OverrideService
# ─────────────────────────────────────────────────────────────

def test_override_service_no_patch_source(tmp_path):
    svc = OverrideService()
    result = svc.execute(tmp_path, patch_source=None)
    assert result == 0


def test_override_service_missing_patch_dir(tmp_path):
    svc = OverrideService()
    result = svc.execute(tmp_path, patch_source=tmp_path / "nope")
    assert result == 0


def test_override_service_copies_files(tmp_path):
    patch_dir = tmp_path / "patches"
    patch_dir.mkdir()
    (patch_dir / "fix.py").write_text("# fix\n")
    (patch_dir / "sub").mkdir()
    (patch_dir / "sub" / "helper.py").write_text("# helper\n")

    repo = tmp_path / "repo"
    repo.mkdir()
    svc = OverrideService()
    count = svc.execute(repo, patch_source=patch_dir)
    assert count == 2
    assert (repo / "fix.py").exists()
    assert (repo / "sub" / "helper.py").exists()


def test_override_service_overwrites_existing(tmp_path):
    patch_dir = tmp_path / "patches"
    patch_dir.mkdir()
    (patch_dir / "config.py").write_text("DEBUG = True\n")
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "config.py").write_text("DEBUG = False\n")
    svc = OverrideService()
    svc.execute(repo, patch_source=patch_dir)
    assert "True" in (repo / "config.py").read_text()


def test_override_service_execute_no_args(tmp_path):
    svc = OverrideService()
    result = svc.execute(tmp_path)
    assert result == 0
