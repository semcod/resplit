"""
Domain Events for rebuild Event Sourcing.

All events are immutable Pydantic models.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


# Legacy PipelineEvent for backward compatibility
@dataclass
class PipelineEvent:
    event_type: str
    timestamp: str
    data: dict

    @classmethod
    def create(cls, event_type: str, **kwargs) -> PipelineEvent:
        return cls(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            data=kwargs
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    aggregate_id: str = ""  # e.g. walk run ID
    occurred_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    version: int = 1

    model_config = ConfigDict(frozen=True)

    def model_post_init(self, __context: Any) -> None:
        if not self.event_type:
            object.__setattr__(self, "event_type", type(self).__name__)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


# ─── Walk events ──────────────────────────────────────────────────────────────

class WalkStartedEvent(DomainEvent):
    repo: str
    days: int
    deploy_method: str
    dry_run: bool = False


class CommitCheckedOutEvent(DomainEvent):
    day: str          # ISO date
    commit_sha: str
    commit_message: str


class DeployStartedEvent(DomainEvent):
    day: str
    commit_sha: str
    deploy_method: str


class DeployFinishedEvent(DomainEvent):
    day: str
    commit_sha: str
    success: bool
    duration_seconds: float = 0.0


class DeployFailedEvent(DomainEvent):
    day: str
    commit_sha: str
    error: str
    error_category: Optional[str] = None


class HealthCheckPassedEvent(DomainEvent):
    day: str
    url: str
    status_code: int
    response_time_ms: float


class HealthCheckFailedEvent(DomainEvent):
    day: str
    url: str
    error: str


class EndpointTestedEvent(DomainEvent):
    day: str
    method: str
    path: str
    status_code: int
    response_time_ms: float
    passed: bool


class DayFinishedEvent(DomainEvent):
    day: str
    deploy_success: bool
    health_pct: float
    endpoints_total: int
    endpoints_passed: int
    duration_seconds: float


class WalkFinishedEvent(DomainEvent):
    total_days: int
    healthy_days: int
    avg_health_pct: float
    output_dir: str


# ─── Analysis events ──────────────────────────────────────────────────────────

class AnalysisStartedEvent(DomainEvent):
    repo: str
    analysis_type: str


class AnalysisFinishedEvent(DomainEvent):
    repo: str
    analysis_type: str
    findings_count: int
    summary: str


# ─── Snapshot events ──────────────────────────────────────────────────────────

class SnapshotCreatedEvent(DomainEvent):
    snapshot_name: str
    db_type: str
    size_bytes: int
    commit_sha: Optional[str] = None


class SnapshotPrunedEvent(DomainEvent):
    pruned_count: int
    remaining_count: int


# ─── Notification events ──────────────────────────────────────────────────────

class NotificationSentEvent(DomainEvent):
    notification_event: str
    hooks_count: int
    sent_count: int
