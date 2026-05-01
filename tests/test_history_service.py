"""Tests for rebuild.application.services.history_service."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from rebuild.application.services.history_service import HistoryService
from rebuild.domain.endpoint import EndpointStatus


def _write_day(results_dir: Path, day: str, results: list, commit_lines: list | None = None):
    day_dir = results_dir / day
    day_dir.mkdir(parents=True)
    (day_dir / "results.json").write_text(json.dumps(results))
    if commit_lines:
        (day_dir / "commit.txt").write_text("\n".join(commit_lines))


# ──────────────────────────────────────────────
# load_history
# ──────────────────────────────────────────────

def test_load_history_empty_dir(tmp_path):
    svc = HistoryService()
    assert svc.load_history(tmp_path / "nonexistent") == []


def test_load_history_no_results_json(tmp_path):
    (tmp_path / "2024-01-01").mkdir()
    svc = HistoryService()
    assert svc.load_history(tmp_path) == []


def test_load_history_single_day(tmp_path):
    _write_day(tmp_path, "2024-03-15", [
        {"method": "GET", "path": "/api/health", "status": "ok", "http_status": 200, "url": "http://localhost:8003"}
    ])
    svc = HistoryService()
    results = svc.load_history(tmp_path)
    assert len(results) == 1
    assert results[0].day == date(2024, 3, 15)
    assert results[0].ok_count == 1
    assert results[0].fail_count == 0


def test_load_history_multiple_days_sorted(tmp_path):
    for day in ("2024-03-13", "2024-03-15", "2024-03-14"):
        _write_day(tmp_path, day, [
            {"method": "GET", "path": "/api/health", "status": "ok", "http_status": 200, "url": ""}
        ])
    svc = HistoryService()
    results = svc.load_history(tmp_path)
    days = [r.day for r in results]
    assert days == sorted(days)


def test_load_history_health_pct(tmp_path):
    _write_day(tmp_path, "2024-03-15", [
        {"method": "GET", "path": "/api/health", "status": "ok", "http_status": 200, "url": ""},
        {"method": "GET", "path": "/api/items", "status": "fail", "http_status": 500, "url": ""},
    ])
    svc = HistoryService()
    results = svc.load_history(tmp_path)
    assert results[0].health_pct == 50.0


def test_load_history_skips_invalid_dir_name(tmp_path):
    (tmp_path / "not-a-date").mkdir()
    ((tmp_path / "not-a-date") / "results.json").write_text("[]")
    _write_day(tmp_path, "2024-03-15", [
        {"method": "GET", "path": "/api/health", "status": "ok", "http_status": 200, "url": ""}
    ])
    svc = HistoryService()
    results = svc.load_history(tmp_path)
    assert len(results) == 1


def test_load_history_with_commit(tmp_path):
    _write_day(tmp_path, "2024-03-15", [
        {"method": "GET", "path": "/api/health", "status": "ok", "http_status": 200, "url": ""}
    ], commit_lines=[
        "abc123def456abc123def456abc123def456abc1",
        "Fix health endpoint",
        "Alice",
        "2024-03-15T10:00:00+00:00",
    ])
    svc = HistoryService()
    results = svc.load_history(tmp_path)
    assert results[0].commit is not None
    assert results[0].commit.sha == "abc123def456abc123def456abc123def456abc1"
    assert results[0].commit.author == "Alice"


def test_load_history_status_timeout(tmp_path):
    _write_day(tmp_path, "2024-03-15", [
        {"method": "GET", "path": "/api/slow", "status": "timeout", "url": ""}
    ])
    svc = HistoryService()
    results = svc.load_history(tmp_path)
    assert results[0].endpoint_results[0].status == EndpointStatus.TIMEOUT


def test_load_history_testql_passed(tmp_path):
    _write_day(tmp_path, "2024-03-15", [
        {"method": "GET", "path": "/api/health", "status": "ok",
         "http_status": 200, "url": "", "testql_passed": True}
    ])
    svc = HistoryService()
    results = svc.load_history(tmp_path)
    assert results[0].endpoint_results[0].testql_passed is True
