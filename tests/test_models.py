"""Tests for rebuild.domain models."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from rebuild.domain.models import DeployMethod, WalkConfig
from rebuild.domain.commit import CommitInfo
from rebuild.domain.day_result import DayResult
from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus


def test_endpoint_url():
    ep = Endpoint(method="GET", path="/api/health", base_url="http://localhost:8003")
    assert ep.url == "http://localhost:8003/api/health"


def test_endpoint_url_strips_trailing_slash():
    ep = Endpoint(method="GET", path="/api/health", base_url="http://localhost:8003/")
    assert ep.url == "http://localhost:8003/api/health"


def test_endpoint_slug():
    ep = Endpoint(method="GET", path="/api/health", base_url="http://localhost:8003")
    assert ep.slug == "GET_api_health"


def test_day_result_health_pct_empty():
    result = DayResult(
        day=date.today(),
        commit=None,
        deploy_method=DeployMethod.NONE,
        deploy_success=False,
    )
    assert result.health_pct == 0.0


def test_day_result_health_pct():
    ep = Endpoint(method="GET", path="/api/health", base_url="http://localhost:8003")
    ep_results = [
        EndpointResult(endpoint=ep, status=EndpointStatus.OK),
        EndpointResult(endpoint=ep, status=EndpointStatus.OK),
        EndpointResult(endpoint=ep, status=EndpointStatus.FAIL),
        EndpointResult(endpoint=ep, status=EndpointStatus.FAIL),
    ]
    result = DayResult(
        day=date.today(),
        commit=None,
        deploy_method=DeployMethod.NONE,
        deploy_success=True,
        endpoint_results=ep_results,
    )
    assert result.ok_count == 2
    assert result.fail_count == 2
    assert result.health_pct == 50.0


def test_walk_config_defaults():
    config = WalkConfig(repo_path=Path("/tmp"))
    assert config.days == 30
    assert config.output_dir == Path(".rebuild")
    assert config.deploy_method == DeployMethod.AUTO
    assert config.dry_run is False


def test_day_result_to_dict_truncates_long_deploy_log():
    log_lines = [f"line {i}" for i in range(250)]
    result = DayResult(
        day=date.today(),
        commit=None,
        deploy_method=DeployMethod.NONE,
        deploy_success=False,
        deploy_log="\n".join(log_lines),
    )

    data = result.to_dict()
    deploy_log = data["deploy"]["log"]

    assert deploy_log is not None
    assert "deploy log truncated" in deploy_log
    assert "line 249" in deploy_log
    assert "line 0" not in deploy_log


def test_day_result_to_dict_keeps_short_deploy_log():
    result = DayResult(
        day=date.today(),
        commit=None,
        deploy_method=DeployMethod.NONE,
        deploy_success=False,
        deploy_log="a\nb\nc",
    )

    data = result.to_dict()
    assert data["deploy"]["log"] == "a\nb\nc"
