"""Snapshot-related CQRS Commands."""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from .base import Command, CommandResult


class CreateSnapshotCommand(Command):
    """Create a DB snapshot."""

    snapshot_dir: str
    db_container: str = "db"
    db_type: str = "postgres"
    db_name: str = "app"
    db_user: str = "postgres"
    name: Optional[str] = None
    commit_sha: Optional[str] = None
    max_snapshots: int = Field(10, ge=0)


class CreateSnapshotCommandResult(CommandResult):
    """Result of CreateSnapshotCommand."""

    snapshot_name: str = ""
    size_bytes: int = 0
    created_at: str = ""


class PruneSnapshotsCommand(Command):
    """Prune old snapshots using LRU policy."""

    snapshot_dir: str
    keep: int = Field(5, ge=0)


class PruneSnapshotsCommandResult(CommandResult):
    """Result of PruneSnapshotsCommand."""

    pruned_count: int = 0
    remaining_count: int = 0
