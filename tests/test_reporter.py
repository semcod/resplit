"""Tests for resplit.reporter."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from resplit.models import (
    CommitInfo,
    DayResult,
    DeployMethod,
    Endpoint,
    EndpointResult,
    EndpointStatus,
)
from resplit.reporter import save_day, save_json, save_html, save_timeline_index


def _make_result(tmp_path: Path) -> DayResult:
    ep = Endpoint(method="GET", path="/api/health", base_url="http://localhost:8003")
    commit = CommitInfo(
        sha="abc123",
        message="Test commit",
        author="Test Author",
        timestamp=datetime(2024, 3, 15, 10, 30),
        date=date(2024, 3, 15),
    )
    return DayResult(
        day=date(2024, 3, 15),
        commit=commit,
        deploy_method=DeployMethod.DOCKER_COMPOSE,
        deploy_success=True,
        endpoints=[ep],
        endpoint_results=[EndpointResult(endpoint=ep, status=EndpointStatus.OK, http_status=200)],
        output_dir=tmp_path / "2024-03-15",
        duration_seconds=5.0,
    )


def test_save_json_creates_files(tmp_path):
    result = _make_result(tmp_path)
    save_json(result)
    day_dir = tmp_path / "2024-03-15"
    assert (day_dir / "commit.txt").exists()
    assert (day_dir / "endpoints.json").exists()
    assert (day_dir / "results.json").exists()


def test_save_json_results_content(tmp_path):
    result = _make_result(tmp_path)
    save_json(result)
    data = json.loads((tmp_path / "2024-03-15" / "results.json").read_text())
    assert len(data) == 1
    assert data[0]["status"] == "ok"
    assert data[0]["http_status"] == 200


def test_save_html_creates_report(tmp_path):
    result = _make_result(tmp_path)
    save_html(result)
    report = tmp_path / "2024-03-15" / "report.html"
    assert report.exists()
    content = report.read_text()
    assert "resplit" in content
    assert "2024-03-15" in content


def test_save_timeline_index(tmp_path):
    result = _make_result(tmp_path)
    save_timeline_index([result], tmp_path)
    index = tmp_path / "index.html"
    assert index.exists()
    content = index.read_text()
    assert "resplit" in content
    assert "2024-03-15" in content
