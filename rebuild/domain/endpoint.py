from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Any, Dict


class EndpointStatus(str, Enum):
    OK = "ok"
    FAIL = "fail"
    FAIL_AUTH = "fail_auth"
    FAIL_TEMPLATE = "fail_template"
    FAIL_SERVER = "fail_server"
    FAIL_NETWORK = "fail_network"
    TIMEOUT = "timeout"
    SKIP = "skip"
    SKIP_METHOD = "skip_method"
    SKIP_AUTH = "skip_auth"
    UNKNOWN = "unknown"


@dataclass
class Endpoint:
    method: str  # GET / POST / ...
    path: str  # /api/health
    base_url: str  # http://localhost:8003
    service: str = ""  # nazwa usługi z deta scan
    description: str = ""
    template_path: Optional[str] = None  # Oryginalna ścieżka z {param}
    body: Optional[Dict[str, Any]] = None

    @property
    def url(self) -> str:
        return self.base_url.rstrip("/") + self.path

    @property
    def slug(self) -> str:
        """Bezpieczna nazwa pliku: GET_api_health"""
        safe = self.path.replace("/", "_").replace("?", "_").strip("_")
        return f"{self.method}_{safe}"


@dataclass
class EndpointResult:
    endpoint: Endpoint
    status: EndpointStatus
    http_status: Optional[int] = None
    response_time_ms: Optional[float] = None
    screenshot_path: Optional[Path] = None
    # Placeholder field for Sprint 4 testql integration (ANALYSIS.md §P1.5).
    # Currently never populated by walk/test pipelines — always serialised as None.
    # Will be populated once `testql` (PyPI v0.6.18) replaces the legacy DSL.
    testql_passed: Optional[bool] = None
    error: Optional[str] = None
    fail_reason: Optional[str] = None
