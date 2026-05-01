from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

class EndpointStatus(str, Enum):
    OK = "ok"
    FAIL = "fail"
    TIMEOUT = "timeout"
    SKIP = "skip"
    UNKNOWN = "unknown"

@dataclass
class Endpoint:
    method: str           # GET / POST / ...
    path: str             # /api/health
    base_url: str         # http://localhost:8003
    service: str = ""     # nazwa usługi z deta scan
    description: str = ""
    template_path: Optional[str] = None # Oryginalna ścieżka z {param}

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
    testql_passed: Optional[bool] = None
    error: Optional[str] = None
