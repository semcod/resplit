"""Tests for rebuild.application.services.test_service."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import httpx

from rebuild.domain.endpoint import Endpoint, EndpointStatus
from rebuild.domain.models import WalkConfig
from rebuild.application.services.test_service import TestService

def _ep(path: str = "/api/health", method: str = "GET") -> Endpoint:
    return Endpoint(method=method, path=path, base_url="http://localhost:8003")

# ──────────────────────────────────────────────
# TestService
# ──────────────────────────────────────────────

def test_test_service_ok():
    ep = _ep("/api/health")
    config = WalkConfig(repo_path=Path("/fake"))
    service = TestService(config)
    
    mock_response = type("R", (), {"status_code": 200, "text": "OK"})()
    with patch.object(service.http, "get", return_value=mock_response) as mock_get:
        results = service.execute([ep])
        # Verify the URL was called correctly
        mock_get.assert_called_once_with(ep.url)
    
    assert len(results) == 1
    assert results[0].status == EndpointStatus.OK
    assert results[0].http_status == 200

def test_test_service_timeout():
    ep = _ep("/api/health")
    config = WalkConfig(repo_path=Path("/fake"))
    service = TestService(config)
    
    with patch.object(service.http, "get", side_effect=httpx.TimeoutException("timeout")):
        results = service.execute([ep])
    
    assert len(results) == 1
    assert results[0].status == EndpointStatus.FAIL

def test_test_service_set_day_dir():
    ep = _ep("/api/health")
    config = WalkConfig(repo_path=Path("/fake"))
    service = TestService(config)
    
    day_dir = Path("/tmp/day")
    service.set_day_dir(day_dir)
    assert service.day_dir == day_dir
