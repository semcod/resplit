"""Tests for rebuild.application.services.reporter_service."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from rebuild.application.services.reporter_service import ReporterService
from rebuild.domain.commit import CommitInfo
from rebuild.domain.day_result import DayResult
from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from rebuild.domain.models import DeployMethod


def _ep(path: str = "/api/health", method: str = "GET") -> Endpoint:
    return Endpoint(method=method, path=path, base_url="http://localhost:8003")


def _day_result(tmp_path: Path, ep_results: list | None = None, commit: CommitInfo | None = None) -> DayResult:
    return DayResult(
        day=date(2024, 3, 15),
        commit=commit,
        deploy_method=DeployMethod.NONE,
        deploy_success=True,
        endpoints=[r.endpoint for r in (ep_results or [])],
        endpoint_results=ep_results or [],
        output_dir=tmp_path / "2024-03-15",
    )


# ──────────────────────────────────────────────
# save_day (new API: results.json is to_dict() format)
# ──────────────────────────────────────────────

def test_save_day_creates_results_file(tmp_path):
    ep = _ep()
    ep_result = EndpointResult(endpoint=ep, status=EndpointStatus.OK, http_status=200, response_time_ms=42.0)
    result = _day_result(tmp_path, [ep_result])
    svc = ReporterService()
    svc.save_day(result)

    results_file = tmp_path / "2024-03-15" / "results.json"
    assert results_file.exists()
    data = json.loads(results_file.read_text())
    assert "results" in data
    assert data["results"][0]["path"] == "/api/health"
    assert data["results"][0]["status"] == "ok"
    assert data["results"][0]["http_status"] == 200


def test_save_day_creates_yaml_and_toon(tmp_path):
    ep = _ep("/api/items", "POST")
    ep_result = EndpointResult(endpoint=ep, status=EndpointStatus.OK)
    result = _day_result(tmp_path, [ep_result])
    svc = ReporterService()
    svc.save_day(result)

    assert (tmp_path / "2024-03-15" / "results.yaml").exists()
    assert (tmp_path / "2024-03-15" / "results.toon").exists()


def test_save_day_includes_commit_in_json(tmp_path):
    commit = CommitInfo(
        sha="abc123def456abc123def456abc123def456abc1",
        message="Fix health endpoint",
        author="Alice",
        timestamp=datetime(2024, 3, 15, 10, 0, 0),
        date=date(2024, 3, 15),
    )
    result = _day_result(tmp_path, commit=commit)
    svc = ReporterService()
    svc.save_day(result)

    data = json.loads((tmp_path / "2024-03-15" / "results.json").read_text())
    assert data["commit"]["sha"] == "abc123def456abc123def456abc123def456abc1"
    assert data["commit"]["message"] == "Fix health endpoint"


def test_save_day_no_output_dir_skips(tmp_path):
    result = DayResult(
        day=date(2024, 3, 15),
        commit=None,
        deploy_method=DeployMethod.NONE,
        deploy_success=True,
        output_dir=None,
    )
    svc = ReporterService()
    svc.save_day(result)  # should not raise


def test_save_day_health_in_json(tmp_path):
    ep = _ep()
    ep_results = [
        EndpointResult(endpoint=ep, status=EndpointStatus.OK),
        EndpointResult(endpoint=ep, status=EndpointStatus.FAIL),
    ]
    result = _day_result(tmp_path, ep_results)
    svc = ReporterService()
    svc.save_day(result)

    data = json.loads((tmp_path / "2024-03-15" / "results.json").read_text())
    assert data["health"]["ok"] == 1
    assert data["health"]["fail"] == 1
    assert data["health"]["percentage"] == 50.0


# ──────────────────────────────────────────────
# save_html
# ──────────────────────────────────────────────

def test_save_html_creates_report_file(tmp_path):
    ep = _ep()
    ep_result = EndpointResult(endpoint=ep, status=EndpointStatus.OK, http_status=200)
    result = _day_result(tmp_path, [ep_result])
    svc = ReporterService()
    svc.save_day(result)

    report = tmp_path / "2024-03-15" / "report.html"
    assert report.exists()
    content = report.read_text()
    assert "2024-03-15" in content
    assert "/api/health" in content


def test_save_html_contains_health_pct(tmp_path):
    ep = _ep()
    ep_results = [
        EndpointResult(endpoint=ep, status=EndpointStatus.OK),
        EndpointResult(endpoint=ep, status=EndpointStatus.FAIL),
    ]
    result = _day_result(tmp_path, ep_results)
    svc = ReporterService()
    svc.save_day(result)

    content = (tmp_path / "2024-03-15" / "report.html").read_text()
    assert "50.0" in content


# ──────────────────────────────────────────────
# save_timeline_index
# ──────────────────────────────────────────────

def test_save_timeline_index_creates_index(tmp_path):
    ep = _ep()
    day_dir = tmp_path / "2024-03-15"
    day_dir.mkdir(parents=True)
    result = DayResult(
        day=date(2024, 3, 15),
        commit=None,
        deploy_method=DeployMethod.NONE,
        deploy_success=True,
        endpoints=[ep],
        endpoint_results=[EndpointResult(endpoint=ep, status=EndpointStatus.OK)],
        output_dir=day_dir,
    )
    svc = ReporterService()
    svc.save_timeline_index([result], tmp_path)

    index = tmp_path / "index.html"
    assert index.exists()
    content = index.read_text()
    assert "2024-03-15" in content
    assert "100.0%" in content


def test_save_timeline_index_multiple_days_sorted(tmp_path):
    days = [date(2024, 3, 13), date(2024, 3, 15), date(2024, 3, 14)]
    results = []
    for d in days:
        day_dir = tmp_path / str(d)
        day_dir.mkdir(parents=True)
        results.append(DayResult(
            day=d, commit=None,
            deploy_method=DeployMethod.NONE, deploy_success=True,
            output_dir=day_dir,
        ))
    svc = ReporterService()
    svc.save_timeline_index(results, tmp_path)
    content = (tmp_path / "index.html").read_text()
    assert content.index("2024-03-15") < content.index("2024-03-13")
