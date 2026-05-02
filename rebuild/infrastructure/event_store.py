"""
SQLite-backed EventStore for Event Sourcing.

Persists all DomainEvents with full JSON payload.
Supports replay, streaming by aggregate, and pruning.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional, Type

from ..domain.events.domain_events import DomainEvent


_DDL = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    TEXT    NOT NULL UNIQUE,
    event_type  TEXT    NOT NULL,
    aggregate_id TEXT   NOT NULL DEFAULT '',
    occurred_at TEXT    NOT NULL,
    version     INTEGER NOT NULL DEFAULT 1,
    payload     TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events (aggregate_id);
CREATE INDEX IF NOT EXISTS idx_events_type      ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_time      ON events (occurred_at);
"""


class EventStore:
    """
    Append-only SQLite event store.

    Usage::

        store = EventStore(Path(".rebuild/events.db"))
        store.append(WalkStartedEvent(aggregate_id="run-1", repo="/repo", days=7, deploy_method="none", dry_run=False))
        for ev in store.load(aggregate_id="run-1"):
            print(ev.event_type, ev.occurred_at)
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(_DDL)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def append(self, event: DomainEvent) -> None:
        """Persist a single domain event."""
        payload = json.dumps(event.to_dict())
        with self._conn() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO events
                   (event_id, event_type, aggregate_id, occurred_at, version, payload)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    event.event_id,
                    event.event_type,
                    event.aggregate_id,
                    event.occurred_at,
                    event.version,
                    payload,
                ),
            )

    def append_many(self, events: List[DomainEvent]) -> None:
        """Bulk append events in a single transaction."""
        rows = [
            (e.event_id, e.event_type, e.aggregate_id, e.occurred_at, e.version,
             json.dumps(e.to_dict()))
            for e in events
        ]
        with self._conn() as conn:
            conn.executemany(
                """INSERT OR IGNORE INTO events
                   (event_id, event_type, aggregate_id, occurred_at, version, payload)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                rows,
            )

    def load(
        self,
        aggregate_id: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[DomainEvent]:
        """
        Load events with optional filters.

        Returns raw DomainEvent base instances (payload preserved in .to_dict()).
        Use load_typed() for concrete types.
        """
        conditions = []
        params: list = []
        if aggregate_id is not None:
            conditions.append("aggregate_id = ?")
            params.append(aggregate_id)
        if event_type is not None:
            conditions.append("event_type = ?")
            params.append(event_type)
        if since is not None:
            conditions.append("occurred_at >= ?")
            params.append(since)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        limit_clause = f"LIMIT {limit}" if limit else ""
        sql = f"SELECT payload FROM events {where} ORDER BY id {limit_clause}"

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        result = []
        for row in rows:
            data = json.loads(row["payload"])
            result.append(DomainEvent(**data))
        return result

    def load_raw(
        self,
        aggregate_id: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[dict]:
        """Load events as raw dicts (for REST/WS serialization)."""
        conditions = []
        params: list = []
        if aggregate_id is not None:
            conditions.append("aggregate_id = ?")
            params.append(aggregate_id)
        if event_type is not None:
            conditions.append("event_type = ?")
            params.append(event_type)
        if since is not None:
            conditions.append("occurred_at >= ?")
            params.append(since)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        limit_clause = f"LIMIT {limit}" if limit else ""
        sql = f"SELECT payload FROM events {where} ORDER BY id {limit_clause}"

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def count(self, aggregate_id: Optional[str] = None) -> int:
        with self._conn() as conn:
            if aggregate_id:
                row = conn.execute(
                    "SELECT COUNT(*) AS n FROM events WHERE aggregate_id=?",
                    (aggregate_id,),
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) AS n FROM events").fetchone()
        return row["n"]

    def prune_before(self, before_iso: str) -> int:
        """Delete events older than *before_iso*. Returns count deleted."""
        with self._conn() as conn:
            cur = conn.execute(
                "DELETE FROM events WHERE occurred_at < ?", (before_iso,)
            )
            return cur.rowcount
