from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional, Dict, Any

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
    is_dry_run: bool = False

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

    def to_dict(self) -> Dict[str, Any]:
        """Serializes result for export."""
        return {
            "day": str(self.day),
            "commit": {
                "sha": self.commit.sha,
                "message": self.commit.message,
                "author": self.commit.author,
                "timestamp": self.commit.timestamp.isoformat()
            } if self.commit else None,
            "health": {
                "percentage": self.health_pct,
                "ok": self.ok_count,
                "fail": self.fail_count,
                "total": len(self.endpoints)
            },
            "performance": {
                "duration_seconds": round(self.duration_seconds, 3)
            },
            "deploy": {
                "method": self.deploy_method.value,
                "success": self.deploy_success,
                "is_dry_run": self.is_dry_run
            },
            "results": [
                {
                    "method": r.endpoint.method,
                    "path": r.endpoint.path,
                    "status": r.status.value,
                    "http_status": r.http_status,
                    "time_ms": r.response_time_ms
                } for r in self.endpoint_results
            ]
        }
