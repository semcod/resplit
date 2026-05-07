"""Coverage tests for rebuild.interfaces.api.app — REST endpoint paths.

Complements ``tests/test_cqrs_arch.py:TestAPISmoke`` by covering the command
dispatch endpoints, query endpoints, and DSL/NLP error branches that the
smoke suite skips.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient   # noqa: E402

from rebuild.interfaces.api.app import create_app   # noqa: E402


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

class _FakeResult:
    """Stand-in for a CQRS result that supports ``.model_dump()``."""

    def __init__(self, payload: dict):
        self._payload = payload

    def model_dump(self) -> dict:
        return dict(self._payload)


def _bus_returning(payload: dict) -> MagicMock:
    bus = MagicMock()
    bus.dispatch.return_value = _FakeResult(payload)
    return bus


# ──────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────

def test_command_walk_dispatches_and_returns_payload():
    bus = _bus_returning({"command_id": "w1", "success": True})
    app = create_app(command_bus=bus)
    client = TestClient(app)

    resp = client.post("/commands/walk", json={
        "repo": "/tmp/repo",
        "days": 7,
        "deploy": "none",
    })
    assert resp.status_code == 200
    assert resp.json() == {"command_id": "w1", "success": True}
    assert bus.dispatch.call_count == 1


def test_command_analyze_dispatches():
    bus = _bus_returning({"command_id": "a1", "success": True})
    app = create_app(command_bus=bus)
    client = TestClient(app)

    resp = client.post("/commands/analyze", json={
        "repo": "/tmp/repo",
        "analysis_type": "duplicates",
    })
    assert resp.status_code == 200
    assert resp.json()["command_id"] == "a1"


def test_command_snapshot_dispatches():
    bus = _bus_returning({"command_id": "s1", "success": True})
    app = create_app(command_bus=bus)
    client = TestClient(app)

    resp = client.post("/commands/snapshot", json={
        "snapshot_dir": "/tmp/snaps",
        "label": "v1",
    })
    assert resp.status_code == 200
    assert resp.json()["command_id"] == "s1"


def test_command_prune_dispatches():
    bus = _bus_returning({"command_id": "p1", "success": True})
    app = create_app(command_bus=bus)
    client = TestClient(app)

    resp = client.post("/commands/prune", json={
        "snapshot_dir": "/tmp/snaps",
        "keep": 5,
    })
    assert resp.status_code == 200
    assert resp.json()["command_id"] == "p1"


# ──────────────────────────────────────────────
# DSL error branches
# ──────────────────────────────────────────────

def test_command_dsl_returns_error_when_parser_raises():
    """The DSL parser raises ValueError for malformed input → API returns success=False."""
    app = create_app()
    client = TestClient(app)

    resp = client.post("/commands/dsl", json={"dsl": "not_a_real_verb foo"})
    assert resp.status_code == 200
    body = resp.json()
    # Either parser raises, or returns None (query verb / unrecognised) → both
    # yield success=False with no command_id.
    assert body.get("success") is False
    assert body.get("command_id") == ""


def test_command_dsl_returns_error_for_query_verb():
    """Query verbs (e.g. 'history') are valid DSL but not commands → graceful 200 + error."""
    app = create_app()
    client = TestClient(app)

    resp = client.post("/commands/dsl", json={"dsl": "history limit:5"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("success") is False


# ──────────────────────────────────────────────
# NLP error branches
# ──────────────────────────────────────────────

def test_command_nlp_returns_error_for_uninterpretable_text():
    """NLPMapper.to_dsl returns empty when text can't be mapped."""
    app = create_app()
    client = TestClient(app)

    resp = client.post("/commands/nlp", json={"text": "????"})
    assert resp.status_code == 200
    body = resp.json()
    # Either the mapper returned empty, or the parser later failed — both → success=False.
    assert body.get("success") is False


# ──────────────────────────────────────────────
# Queries
# ──────────────────────────────────────────────

def test_query_history_dispatches_with_default_params():
    qbus = _bus_returning({"results": [], "count": 0})
    app = create_app(query_bus=qbus)
    client = TestClient(app)

    resp = client.get("/queries/history")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0
    assert qbus.dispatch.call_count == 1


def test_query_history_passes_explicit_params():
    qbus = _bus_returning({"results": [{"day": "2026-05-01"}], "count": 1})
    app = create_app(query_bus=qbus)
    client = TestClient(app)

    resp = client.get(
        "/queries/history",
        params={"results_dir": "out", "limit": 10,
                "date_from": "2026-04-01", "date_to": "2026-05-01"},
    )
    assert resp.status_code == 200
    assert resp.json()["count"] == 1
    # Check the query object the bus received
    qry = qbus.dispatch.call_args[0][0]
    assert qry.results_dir == "out"
    assert qry.limit == 10
    assert qry.date_from == "2026-04-01"
    assert qry.date_to == "2026-05-01"


def test_query_day_dispatches():
    qbus = _bus_returning({"day": "2026-05-01", "endpoints": []})
    app = create_app(query_bus=qbus)
    client = TestClient(app)

    resp = client.get("/queries/day/2026-05-01", params={"results_dir": "out"})
    assert resp.status_code == 200
    qry = qbus.dispatch.call_args[0][0]
    assert qry.day == "2026-05-01"
    assert qry.results_dir == "out"


def test_query_snapshots_dispatches():
    qbus = _bus_returning({"count": 3, "total_size_mb": 12.5})
    app = create_app(query_bus=qbus)
    client = TestClient(app)

    resp = client.get("/queries/snapshots", params={"snapshot_dir": "/tmp/snaps"})
    assert resp.status_code == 200
    assert resp.json()["count"] == 3
    qry = qbus.dispatch.call_args[0][0]
    assert qry.snapshot_dir == "/tmp/snaps"


def test_query_plugins_dispatches_without_group():
    qbus = _bus_returning({"plugins": [], "count": 0})
    app = create_app(query_bus=qbus)
    client = TestClient(app)

    resp = client.get("/queries/plugins")
    assert resp.status_code == 200
    qry = qbus.dispatch.call_args[0][0]
    assert qry.group is None


def test_query_plugins_dispatches_with_group():
    qbus = _bus_returning({"plugins": ["a", "b"], "count": 2})
    app = create_app(query_bus=qbus)
    client = TestClient(app)

    resp = client.get("/queries/plugins", params={"group": "rebuild.scanners"})
    assert resp.status_code == 200
    qry = qbus.dispatch.call_args[0][0]
    assert qry.group == "rebuild.scanners"


# ──────────────────────────────────────────────
# Health & smoke
# ──────────────────────────────────────────────

def test_app_creation_with_all_buses_injected():
    cb = MagicMock()
    qb = MagicMock()
    eb = MagicMock()
    es = MagicMock()
    app = create_app(command_bus=cb, query_bus=qb, event_bus=eb, event_store=es)
    assert app.title == "rebuild API"


def test_health_endpoint_returns_ok():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "rebuild-api"}
