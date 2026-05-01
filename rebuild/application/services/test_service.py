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
        # 1. Try TestQL if available
        # (Simplified for now)
        
        # 2. Fallback to HTTP Probe
        try:
            url = ep.url
            resp = self.http.get(url)
            status = EndpointStatus.OK if resp.status_code < 400 else EndpointStatus.FAIL
            return EndpointResult(
                endpoint=ep,
                status=status,
                http_status=resp.status_code
            )
        except Exception as e:
            return EndpointResult(
                endpoint=ep,
                status=EndpointStatus.FAIL,
                error=str(e)
            )
