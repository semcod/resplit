from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

from .commit import CommitInfo
from .endpoint import Endpoint, EndpointResult, EndpointStatus
from .models import DeployMethod


_DEPLOY_LOG_MAX_LINES = 200


class DeployErrorCategory(str, Enum):
    COMPOSE_BUILD_FAIL = "compose_build_fail"
    PORT_CONFLICT = "port_conflict"
    MIGRATION_FAIL = "migration_fail"
    HEALTH_TIMEOUT = "health_timeout"
    MISSING_ENV = "missing_env"
    UNKNOWN = "unknown"


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
    deploy_log: Optional[str] = None
    deploy_error_category: Optional[DeployErrorCategory] = None
    duration_seconds: float = 0.0
    is_dry_run: bool = False

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.endpoint_results if r.status == EndpointStatus.OK)

    @property
    def fail_count(self) -> int:
        _fail = {
            EndpointStatus.FAIL,
            EndpointStatus.FAIL_AUTH,
            EndpointStatus.FAIL_SERVER,
            EndpointStatus.FAIL_NETWORK,
            EndpointStatus.FAIL_TEMPLATE,
        }
        return sum(1 for r in self.endpoint_results if r.status in _fail)

    @property
    def health_pct(self) -> float:
        total = len(self.endpoint_results)
        return round(self.ok_count / total * 100, 1) if total else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serializes result for export."""
        deploy_log = self.deploy_log
        if deploy_log:
            lines = deploy_log.splitlines()
            if len(lines) > _DEPLOY_LOG_MAX_LINES:
                omitted = len(lines) - _DEPLOY_LOG_MAX_LINES
                tail = "\n".join(lines[-_DEPLOY_LOG_MAX_LINES:])
                deploy_log = (
                    f"[rebuild] deploy log truncated: omitted {omitted} lines; "
                    f"showing last {_DEPLOY_LOG_MAX_LINES} lines\n{tail}"
                )

        return {
            "day": str(self.day),
            "commit": {
                "sha": self.commit.sha,
                "message": self.commit.message,
                "author": self.commit.author,
                "timestamp": self.commit.timestamp.isoformat(),
            }
            if self.commit
            else None,
            "health": {
                "percentage": self.health_pct,
                "ok": self.ok_count,
                "fail": self.fail_count,
                "total": len(self.endpoints),
            },
            "performance": {"duration_seconds": round(self.duration_seconds, 3)},
            "deploy": {
                "method": self.deploy_method.value,
                "success": self.deploy_success,
                "is_dry_run": self.is_dry_run,
                "log": deploy_log,
                "error_category": self.deploy_error_category.value
                if self.deploy_error_category
                else None,
            },
            "results": [
                {
                    "method": r.endpoint.method,
                    "path": r.endpoint.path,
                    "status": r.status.value,
                    "http_status": r.http_status,
                    "time_ms": r.response_time_ms,
                    "fail_reason": r.fail_reason,
                    "template_path": r.endpoint.template_path,
                }
                for r in self.endpoint_results
            ],
        }
