from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from .commit import CommitInfo
from .endpoint import Endpoint, EndpointResult, EndpointStatus
from .models import DeployMethod

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
