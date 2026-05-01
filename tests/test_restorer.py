"""Tests for resplit.restorer."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from resplit.restorer import find_last_working_day, _find_backend_files, _is_page_endpoint


def _make_results_dir(tmp_path: Path, day: str, endpoint: str, status: str) -> None:
    day_dir = tmp_path / day
    day_dir.mkdir(parents=True)
    results = [{"path": endpoint, "method": "GET", "url": f"http://localhost{endpoint}", "status": status}]
    (day_dir / "results.json").write_text(json.dumps(results))


def test_find_last_working_day_found(tmp_path):
    _make_results_dir(tmp_path, "2024-03-14", "/api/health", "ok")
    _make_results_dir(tmp_path, "2024-03-15", "/api/health", "fail")
    result = find_last_working_day("/api/health", tmp_path)
    assert result == date(2024, 3, 14)


def test_find_last_working_day_not_found(tmp_path):
    _make_results_dir(tmp_path, "2024-03-15", "/api/health", "fail")
    result = find_last_working_day("/api/health", tmp_path)
    assert result is None


def test_find_backend_files(tmp_path):
    py_file = tmp_path / "router.py"
    py_file.write_text('app.get("/api/health")\ndef health(): pass')
    other = tmp_path / "other.py"
    other.write_text("def nothing(): pass")
    files = _find_backend_files(tmp_path, "/api/health")
    assert py_file in files
    assert other not in files


def test_is_page_endpoint():
    assert _is_page_endpoint("/about") is True
    assert _is_page_endpoint("/api/health") is False
    assert _is_page_endpoint("/webhook/github") is False
