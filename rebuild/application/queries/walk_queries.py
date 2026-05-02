"""Walk / history / snapshot queries."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import Query, QueryResult


class GetWalkHistoryQuery(Query):
    """Get historical walk results from output directory."""

    results_dir: str = ".rebuild"
    limit: int = Field(100, ge=1, le=10000)
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class WalkHistoryResult(QueryResult):
    """Result of GetWalkHistoryQuery."""

    results: List[Dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    avg_health_pct: float = 0.0


class GetDayResultQuery(Query):
    """Get results for a single day."""

    results_dir: str = ".rebuild"
    day: str  # ISO date: 2025-01-15


class DayResultQueryResult(QueryResult):
    """Result of GetDayResultQuery."""

    day: str = ""
    found: bool = False
    data: Dict[str, Any] = Field(default_factory=dict)


class GetSnapshotStatsQuery(Query):
    """Get statistics about saved DB snapshots."""

    snapshot_dir: str


class SnapshotStatsResult(QueryResult):
    """Result of GetSnapshotStatsQuery."""

    count: int = 0
    total_size_bytes: int = 0
    oldest: Optional[str] = None
    newest: Optional[str] = None
    max_snapshots: int = 0
    snapshots: List[Dict[str, Any]] = Field(default_factory=list)


class GetPluginsQuery(Query):
    """List installed plugins."""

    group: Optional[str] = None  # None = all, "scanners", "reporters"


class PluginsQueryResult(QueryResult):
    """Result of GetPluginsQuery."""

    scanners: List[Dict[str, str]] = Field(default_factory=list)
    reporters: List[Dict[str, str]] = Field(default_factory=list)
