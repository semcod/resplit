from __future__ import annotations
from pathlib import Path
from typing import List, Optional

from ...domain.models import WalkConfig
from ...domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from .base import Service
from ...infrastructure.http_adapter import HttpAdapter

class TestService(Service[List[Endpoint], List[EndpointResult]]):
    """
    Service for testing endpoints using various strategies.
    Uses HttpAdapter for standard probes.
    """
    def __init__(self, config: WalkConfig, http: Optional[HttpAdapter] = None):
        self.config = config
        self.http = http or HttpAdapter()
        self.day_dir: Optional[Path] = None

    def set_day_dir(self, day_dir: Path):
        self.day_dir = day_dir

    def execute(self, endpoints: List[Endpoint]) -> List[EndpointResult]:
        results = []
        for ep in endpoints:
            result = self._test_endpoint(ep)
            results.append(result)
        return results

    def _test_endpoint(self, ep: Endpoint) -> EndpointResult:
        if self.config.dry_run:
            return EndpointResult(endpoint=ep, status=EndpointStatus.SKIP)

        try:
            headers = self.config.auth
            method = (ep.method or "GET").upper()
            body = ep.body if isinstance(ep.body, dict) else None

            if method == "GET":
                resp = self.http.get(ep.url, headers=headers)
            elif method == "POST":
                resp = self.http.post(ep.url, json=body, headers=headers)
            elif method == "PUT":
                resp = self.http.put(ep.url, json=body, headers=headers)
            elif method == "PATCH":
                resp = self.http.patch(ep.url, json=body, headers=headers)
            elif method == "DELETE":
                resp = self.http.delete(ep.url, headers=headers)
            else:
                resp = self.http.get(ep.url, headers=headers)

            status = EndpointStatus.OK if resp.status_code < 400 else EndpointStatus.FAIL
            return EndpointResult(
                endpoint=ep,
                status=status,
                http_status=resp.status_code,
                response_time_ms=resp.elapsed.total_seconds() * 1000 if getattr(resp, "elapsed", None) else None,
            )
        except Exception as e:
            return EndpointResult(
                endpoint=ep,
                status=EndpointStatus.FAIL,
                error=str(e)
            )
