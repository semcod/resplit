"""Domain events for Event Sourcing."""

from .domain_events import (
    DomainEvent,
    WalkStartedEvent,
    CommitCheckedOutEvent,
    DeployStartedEvent,
    DeployFinishedEvent,
    DeployFailedEvent,
    HealthCheckPassedEvent,
    HealthCheckFailedEvent,
    EndpointTestedEvent,
    DayFinishedEvent,
    WalkFinishedEvent,
    AnalysisStartedEvent,
    AnalysisFinishedEvent,
    SnapshotCreatedEvent,
    SnapshotPrunedEvent,
    NotificationSentEvent,
    PipelineEvent,  # Legacy for backward compatibility
)

__all__ = [
    "DomainEvent",
    "WalkStartedEvent",
    "CommitCheckedOutEvent",
    "DeployStartedEvent",
    "DeployFinishedEvent",
    "DeployFailedEvent",
    "HealthCheckPassedEvent",
    "HealthCheckFailedEvent",
    "EndpointTestedEvent",
    "DayFinishedEvent",
    "WalkFinishedEvent",
    "AnalysisStartedEvent",
    "AnalysisFinishedEvent",
    "SnapshotCreatedEvent",
    "SnapshotPrunedEvent",
    "NotificationSentEvent",
    "PipelineEvent",
]
