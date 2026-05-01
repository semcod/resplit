"""
retrodep.models — shared data structures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class DeployMethod(str, Enum):
    DOCKER_COMPOSE = "docker-compose"
    UVICORN = "uvicorn"
    CUSTOM = "custom"
    NONE = "none"


class EndpointStatus(str, Enum):
    OK = "ok"
    FAIL = "fail"
    TIMEOUT = "timeout"
    SKIP = "skip"
    UNKNOWN = "unknown"


@dataclass
class CommitInfo:
    sha: str
    message: str
    author: str
    timestamp: datetime
    date: date


@dataclass
class Endpoint:
    method: str           # GET / POST / ...
    path: str             # /api/health
    base_url: str         # http://localhost:8003
    service: str = ""     # nazwa usługi z deta scan
    description: str = ""

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


@dataclass
class DayResult:
    day: date
    commit: Optional[CommitInfo]
    deploy_method: DeployMethod
    deploy_success: bool
    endpoints: list[Endpoint] = field(default_factory=list)
    endpoint_results: list[EndpointResult] = field(default_factory=list)
    output_dir: Optional[Path] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.endpoint_results if r.status == EndpointStatus.OK)

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.endpoint_results if r.status == EndpointStatus.FAIL)

    @property
    def health_pct(self) -> float:
        total = len(self.endpoint_results)
        return round(self.ok_count / total * 100, 1) if total else 0.0


@dataclass
class WalkConfig:
    repo_path: Path
    output_dir: Path = Path(".retrodep")
    days: int = 30
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    deploy_method: DeployMethod = DeployMethod.DOCKER_COMPOSE
    compose_file: str = "docker-compose.yml"
    health_url: str = "http://localhost:8003/api/health"
    health_timeout: int = 60
    health_interval: float = 2.0
    base_url: str = "http://localhost:8003"
    testql_dir: Optional[Path] = None
    screenshots: bool = True
    dry_run: bool = False
    earliest_commit_per_day: bool = True
