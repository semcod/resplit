"""Tests for rebuild.application.services.restore_service."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from rebuild.application.services.restore_service import RestoreService


def _write_day(results_dir: Path, day: str, results: list):
    day_dir = results_dir / day
    day_dir.mkdir(parents=True)
    (day_dir / "results.json").write_text(json.dumps(results))
    return day_dir


# ──────────────────────────────────────────────
# find_last_working_day
# ──────────────────────────────────────────────

def test_find_last_working_day_found(tmp_path):
    results_dir = tmp_path / ".rebuild"
    _write_day(results_dir, "2024-03-14", [
        {"path": "/api/health", "status": "ok"}
    ])
    _write_day(results_dir, "2024-03-15", [
        {"path": "/api/health", "status": "fail"}
    ])
    svc = RestoreService(tmp_path)
    best = svc.find_last_working_day("/api/health", results_dir)
    assert best == date(2024, 3, 14)


def test_find_last_working_day_picks_most_recent(tmp_path):
    results_dir = tmp_path / ".rebuild"
    _write_day(results_dir, "2024-03-13", [{"path": "/api/health", "status": "ok"}])
    _write_day(results_dir, "2024-03-14", [{"path": "/api/health", "status": "ok"}])
    _write_day(results_dir, "2024-03-15", [{"path": "/api/health", "status": "fail"}])
    svc = RestoreService(tmp_path)
    best = svc.find_last_working_day("/api/health", results_dir)
    assert best == date(2024, 3, 14)


def test_find_last_working_day_none_when_always_fail(tmp_path):
    results_dir = tmp_path / ".rebuild"
    _write_day(results_dir, "2024-03-15", [{"path": "/api/health", "status": "fail"}])
    svc = RestoreService(tmp_path)
    best = svc.find_last_working_day("/api/health", results_dir)
    assert best is None


def test_find_last_working_day_missing_dir(tmp_path):
    svc = RestoreService(tmp_path)
    best = svc.find_last_working_day("/api/health", tmp_path / "nonexistent")
    assert best is None


def test_find_last_working_day_ignores_other_endpoints(tmp_path):
    results_dir = tmp_path / ".rebuild"
    _write_day(results_dir, "2024-03-15", [
        {"path": "/api/items", "status": "ok"},
        {"path": "/api/health", "status": "fail"},
    ])
    svc = RestoreService(tmp_path)
    best = svc.find_last_working_day("/api/health", results_dir)
    assert best is None


def test_find_last_working_day_skips_invalid_dirs(tmp_path):
    results_dir = tmp_path / ".rebuild"
    bad_dir = results_dir / "not-a-date"
    bad_dir.mkdir(parents=True)
    (bad_dir / "results.json").write_text(json.dumps([{"path": "/api/health", "status": "ok"}]))
    _write_day(results_dir, "2024-03-15", [{"path": "/api/health", "status": "ok"}])
    svc = RestoreService(tmp_path)
    best = svc.find_last_working_day("/api/health", results_dir)
    assert best == date(2024, 3, 15)


# ──────────────────────────────────────────────
# execute
# ──────────────────────────────────────────────

def test_execute_returns_date(tmp_path):
    results_dir = tmp_path / ".rebuild"
    _write_day(results_dir, "2024-03-15", [{"path": "/api/health", "status": "ok"}])
    svc = RestoreService(tmp_path)
    result = svc.execute(("/api/health", results_dir))
    assert result == date(2024, 3, 15)
