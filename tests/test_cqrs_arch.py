"""
Tests for CQRS Commands, Queries, Event Sourcing, EventBus, DSL v2, NLP.
"""
from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ─── Commands ──────────────────────────────────────────────────────────────

class TestCommandBase:
    def test_command_has_id_and_timestamp(self):
        from rebuild.application.commands.base import Command
        class MyCmd(Command):
            value: str = "x"
        c = MyCmd()
        assert c.command_id
        assert c.issued_at

    def test_command_bus_dispatch(self):
        from rebuild.application.commands.base import (
            Command, CommandResult, CommandHandler, CommandBus
        )
        class PingCommand(Command):
            pass
        class PingResult(CommandResult):
            pong: bool = False
        class PingHandler(CommandHandler):
            def handle(self, cmd):
                return PingResult(command_id=cmd.command_id, success=True, pong=True)

        bus = CommandBus()
        bus.register(PingCommand, PingHandler())
        result = bus.dispatch(PingCommand())
        assert result.success is True
        assert result.pong is True

    def test_command_bus_no_handler_raises(self):
        from rebuild.application.commands.base import Command, CommandBus
        class OrphanCmd(Command):
            pass
        bus = CommandBus()
        with pytest.raises(ValueError, match="No handler registered"):
            bus.dispatch(OrphanCmd())

    def test_multiple_handlers(self):
        from rebuild.application.commands.base import (
            Command, CommandResult, CommandHandler, CommandBus
        )
        results = []
        class CmdA(Command):
            pass
        class CmdB(Command):
            pass
        class ResA(CommandResult):
            pass
        class ResB(CommandResult):
            pass
        class HA(CommandHandler):
            def handle(self, c): return ResA(command_id=c.command_id, success=True)
        class HB(CommandHandler):
            def handle(self, c): return ResB(command_id=c.command_id, success=True)
        bus = CommandBus()
        bus.register(CmdA, HA())
        bus.register(CmdB, HB())
        assert isinstance(bus.dispatch(CmdA()), ResA)
        assert isinstance(bus.dispatch(CmdB()), ResB)


class TestWalkCommand:
    def test_valid_walk_command(self, tmp_path):
        (tmp_path / ".git").mkdir()
        from rebuild.application.commands.walk_commands import WalkCommand
        cmd = WalkCommand(repo=str(tmp_path), days=7, deploy="none")
        assert cmd.days == 7
        assert cmd.deploy == "none"

    def test_invalid_deploy_raises(self, tmp_path):
        from rebuild.application.commands.walk_commands import WalkCommand
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="deploy"):
            WalkCommand(repo=str(tmp_path), days=7, deploy="ftp")

    def test_days_minimum(self, tmp_path):
        from rebuild.application.commands.walk_commands import WalkCommand
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            WalkCommand(repo=str(tmp_path), days=0)

    def test_notifications_default_empty(self, tmp_path):
        from rebuild.application.commands.walk_commands import WalkCommand
        (tmp_path / ".git").mkdir()
        cmd = WalkCommand(repo=str(tmp_path))
        assert cmd.notifications == []

    def test_walk_result_fields(self):
        from rebuild.application.commands.walk_commands import WalkCommandResult
        r = WalkCommandResult(command_id="x", success=True, total_days=7, healthy_days=5, avg_health_pct=71.4)
        assert r.healthy_days == 5
        assert r.avg_health_pct == pytest.approx(71.4)


class TestAnalyzeCommand:
    def test_valid(self, tmp_path):
        from rebuild.application.commands.analyze_commands import AnalyzeCommand
        cmd = AnalyzeCommand(repo=str(tmp_path), analysis_type="duplicates")
        assert cmd.analysis_type == "duplicates"

    def test_invalid_type(self, tmp_path):
        from rebuild.application.commands.analyze_commands import AnalyzeCommand
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AnalyzeCommand(repo=str(tmp_path), analysis_type="magic")

    def test_semantic_threshold_bounds(self, tmp_path):
        from rebuild.application.commands.analyze_commands import AnalyzeCommand
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AnalyzeCommand(repo=str(tmp_path), semantic_threshold=1.5)


class TestSnapshotCommands:
    def test_create_snapshot_command(self):
        from rebuild.application.commands.snapshot_commands import CreateSnapshotCommand
        cmd = CreateSnapshotCommand(snapshot_dir="/snaps", db_type="sqlite")
        assert cmd.db_type == "sqlite"
        assert cmd.max_snapshots == 10

    def test_prune_command(self):
        from rebuild.application.commands.snapshot_commands import PruneSnapshotsCommand
        cmd = PruneSnapshotsCommand(snapshot_dir="/snaps", keep=3)
        assert cmd.keep == 3

    def test_prune_keep_minimum(self):
        from rebuild.application.commands.snapshot_commands import PruneSnapshotsCommand
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            PruneSnapshotsCommand(snapshot_dir="/snaps", keep=-1)


# ─── Queries ──────────────────────────────────────────────────────────────────

class TestQueryBase:
    def test_query_has_id(self):
        from rebuild.application.queries.base import Query
        class Q(Query):
            pass
        q = Q()
        assert q.query_id
        assert q.issued_at

    def test_query_bus_dispatch(self):
        from rebuild.application.queries.base import Query, QueryResult, QueryHandler, QueryBus
        class PingQuery(Query):
            pass
        class PingQResult(QueryResult):
            alive: bool = False
        class PingQHandler(QueryHandler):
            def handle(self, q):
                return PingQResult(query_id=q.query_id, alive=True)
        bus = QueryBus()
        bus.register(PingQuery, PingQHandler())
        r = bus.dispatch(PingQuery())
        assert r.alive is True

    def test_query_bus_no_handler_raises(self):
        from rebuild.application.queries.base import Query, QueryBus
        class Q(Query):
            pass
        bus = QueryBus()
        with pytest.raises(ValueError, match="No handler registered"):
            bus.dispatch(Q())


class TestWalkQueries:
    def test_get_walk_history_defaults(self):
        from rebuild.application.queries.walk_queries import GetWalkHistoryQuery
        q = GetWalkHistoryQuery()
        assert q.results_dir == ".rebuild"
        assert q.limit == 100

    def test_get_day_result(self):
        from rebuild.application.queries.walk_queries import GetDayResultQuery
        q = GetDayResultQuery(day="2025-01-15", results_dir=".rebuild")
        assert q.day == "2025-01-15"

    def test_snapshot_stats_query(self):
        from rebuild.application.queries.walk_queries import GetSnapshotStatsQuery
        q = GetSnapshotStatsQuery(snapshot_dir="/snaps")
        assert q.snapshot_dir == "/snaps"

    def test_plugins_query(self):
        from rebuild.application.queries.walk_queries import GetPluginsQuery
        q = GetPluginsQuery(group="scanners")
        assert q.group == "scanners"


# ─── Domain Events ────────────────────────────────────────────────────────────

class TestDomainEvents:
    def test_event_has_id_and_timestamp(self):
        from rebuild.domain.events import WalkStartedEvent
        e = WalkStartedEvent(
            aggregate_id="r1", repo="/repo", days=7,
            deploy_method="none", dry_run=False
        )
        assert e.event_id
        assert e.occurred_at
        assert e.event_type == "WalkStartedEvent"

    def test_event_frozen(self):
        from rebuild.domain.events import WalkStartedEvent
        e = WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none")
        with pytest.raises(Exception):
            e.repo = "/other"  # type: ignore

    def test_to_dict(self):
        from rebuild.domain.events import DayFinishedEvent
        e = DayFinishedEvent(
            aggregate_id="r1", day="2025-01-01",
            deploy_success=True, health_pct=90.0,
            endpoints_total=5, endpoints_passed=5, duration_seconds=12.3
        )
        d = e.to_dict()
        assert d["event_type"] == "DayFinishedEvent"
        assert d["day"] == "2025-01-01"
        assert d["health_pct"] == 90.0

    def test_all_event_types_importable(self):
        from rebuild.domain.events import (
            WalkStartedEvent, CommitCheckedOutEvent,
            DeployStartedEvent, DeployFinishedEvent, DeployFailedEvent,
            HealthCheckPassedEvent, HealthCheckFailedEvent,
            EndpointTestedEvent, DayFinishedEvent, WalkFinishedEvent,
            AnalysisStartedEvent, AnalysisFinishedEvent,
            SnapshotCreatedEvent, SnapshotPrunedEvent, NotificationSentEvent,
        )

    def test_walk_finished_event(self):
        from rebuild.domain.events import WalkFinishedEvent
        e = WalkFinishedEvent(
            aggregate_id="r1", total_days=14, healthy_days=12,
            avg_health_pct=85.7, output_dir=".rebuild"
        )
        assert e.healthy_days == 12

    def test_deploy_failed_event(self):
        from rebuild.domain.events import DeployFailedEvent
        e = DeployFailedEvent(
            aggregate_id="r1", day="2025-01-01",
            commit_sha="abc123", error="timeout", error_category="network"
        )
        assert e.error_category == "network"


# ─── EventStore ────────────────────────────────────────────────────────────────

class TestEventStore:
    def test_append_and_load(self, tmp_path):
        from rebuild.infrastructure.event_store import EventStore
        from rebuild.domain.events import WalkStartedEvent
        store = EventStore(tmp_path / "events.db")
        e = WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none")
        store.append(e)
        loaded = store.load(aggregate_id="r1")
        assert len(loaded) == 1
        assert loaded[0].event_type == "WalkStartedEvent"

    def test_append_many(self, tmp_path):
        from rebuild.infrastructure.event_store import EventStore
        from rebuild.domain.events import WalkStartedEvent, DayFinishedEvent
        store = EventStore(tmp_path / "events.db")
        events = [
            WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"),
            DayFinishedEvent(
                aggregate_id="r1", day="2025-01-01",
                deploy_success=True, health_pct=80.0,
                endpoints_total=3, endpoints_passed=3, duration_seconds=5.0
            ),
        ]
        store.append_many(events)
        assert store.count(aggregate_id="r1") == 2

    def test_idempotent_append(self, tmp_path):
        from rebuild.infrastructure.event_store import EventStore
        from rebuild.domain.events import WalkStartedEvent
        store = EventStore(tmp_path / "events.db")
        e = WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none")
        store.append(e)
        store.append(e)  # duplicate — should be ignored
        assert store.count() == 1

    def test_filter_by_event_type(self, tmp_path):
        from rebuild.infrastructure.event_store import EventStore
        from rebuild.domain.events import WalkStartedEvent, DeployFailedEvent
        store = EventStore(tmp_path / "events.db")
        store.append(WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"))
        store.append(DeployFailedEvent(aggregate_id="r1", day="2025-01-01", commit_sha="x", error="e"))
        fails = store.load(event_type="DeployFailedEvent")
        assert len(fails) == 1

    def test_load_raw_returns_dicts(self, tmp_path):
        from rebuild.infrastructure.event_store import EventStore
        from rebuild.domain.events import WalkStartedEvent
        store = EventStore(tmp_path / "events.db")
        store.append(WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"))
        raw = store.load_raw()
        assert isinstance(raw[0], dict)
        assert raw[0]["event_type"] == "WalkStartedEvent"

    def test_prune_before(self, tmp_path):
        from rebuild.infrastructure.event_store import EventStore
        from rebuild.domain.events import WalkStartedEvent
        store = EventStore(tmp_path / "events.db")
        e = WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none")
        store.append(e)
        # prune everything before far future
        deleted = store.prune_before("2099-01-01T00:00:00+00:00")
        assert deleted == 1
        assert store.count() == 0

    def test_count_all(self, tmp_path):
        from rebuild.infrastructure.event_store import EventStore
        from rebuild.domain.events import WalkStartedEvent, WalkFinishedEvent
        store = EventStore(tmp_path / "events.db")
        store.append(WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"))
        store.append(WalkFinishedEvent(
            aggregate_id="r1", total_days=7, healthy_days=5,
            avg_health_pct=71.0, output_dir=".rebuild"
        ))
        assert store.count() == 2

    def test_persists_across_instances(self, tmp_path):
        from rebuild.infrastructure.event_store import EventStore
        from rebuild.domain.events import WalkStartedEvent
        db = tmp_path / "events.db"
        s1 = EventStore(db)
        s1.append(WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"))
        s2 = EventStore(db)
        assert s2.count() == 1


# ─── EventBus ─────────────────────────────────────────────────────────────────

class TestEventBus:
    def test_sync_subscriber(self):
        from rebuild.infrastructure.event_bus import EventBus
        from rebuild.domain.events import WalkStartedEvent
        bus = EventBus()
        received = []
        bus.subscribe(WalkStartedEvent, lambda e: received.append(e))
        e = WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none")
        bus.publish(e)
        assert len(received) == 1
        assert received[0].aggregate_id == "r1"

    def test_global_subscriber(self):
        from rebuild.infrastructure.event_bus import EventBus
        from rebuild.domain.events import WalkStartedEvent, WalkFinishedEvent
        bus = EventBus()
        received = []
        bus.subscribe_all(received.append)
        bus.publish(WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"))
        bus.publish(WalkFinishedEvent(aggregate_id="r1", total_days=7, healthy_days=7, avg_health_pct=100.0, output_dir=".r"))
        assert len(received) == 2

    def test_typed_subscriber_not_called_for_other_type(self):
        from rebuild.infrastructure.event_bus import EventBus
        from rebuild.domain.events import WalkStartedEvent, WalkFinishedEvent
        bus = EventBus()
        received = []
        bus.subscribe(WalkFinishedEvent, received.append)
        bus.publish(WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"))
        assert received == []

    def test_unsubscribe(self):
        from rebuild.infrastructure.event_bus import EventBus
        from rebuild.domain.events import WalkStartedEvent
        bus = EventBus()
        received = []
        handler = received.append
        bus.subscribe(WalkStartedEvent, handler)
        bus.unsubscribe(WalkStartedEvent, handler)
        bus.publish(WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"))
        assert received == []

    def test_event_store_integration(self, tmp_path):
        from rebuild.infrastructure.event_bus import EventBus
        from rebuild.infrastructure.event_store import EventStore
        from rebuild.domain.events import WalkStartedEvent
        store = EventStore(tmp_path / "ev.db")
        bus = EventBus(event_store=store)
        bus.publish(WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"))
        assert store.count() == 1

    def test_ws_queue_receives_events(self):
        from rebuild.infrastructure.event_bus import EventBus
        from rebuild.domain.events import WalkStartedEvent
        bus = EventBus()

        async def run():
            q = bus.create_ws_queue()
            bus.publish(WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"))
            event = q.get_nowait()
            return event

        event = asyncio.run(run())
        assert event.event_type == "WalkStartedEvent"

    def test_remove_ws_queue(self):
        from rebuild.infrastructure.event_bus import EventBus
        bus = EventBus()

        async def run():
            q = bus.create_ws_queue()
            assert bus.ws_queue_count == 1
            bus.remove_ws_queue(q)
            assert bus.ws_queue_count == 0

        asyncio.run(run())

    def test_publish_many(self):
        from rebuild.infrastructure.event_bus import EventBus
        from rebuild.domain.events import WalkStartedEvent, WalkFinishedEvent
        bus = EventBus()
        received = []
        bus.subscribe_all(received.append)
        bus.publish_many([
            WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"),
            WalkFinishedEvent(aggregate_id="r1", total_days=7, healthy_days=7, avg_health_pct=100.0, output_dir=".r"),
        ])
        assert len(received) == 2

    def test_handler_exception_does_not_crash_bus(self):
        from rebuild.infrastructure.event_bus import EventBus
        from rebuild.domain.events import WalkStartedEvent
        bus = EventBus()
        bus.subscribe(WalkStartedEvent, lambda e: 1/0)
        received = []
        bus.subscribe_all(received.append)
        bus.publish(WalkStartedEvent(aggregate_id="r1", repo="/r", days=7, deploy_method="none"))
        assert len(received) == 1  # global handler still called

    def test_get_and_set_default_bus(self):
        from rebuild.infrastructure.event_bus import get_event_bus, set_event_bus, EventBus
        bus = EventBus()
        set_event_bus(bus)
        assert get_event_bus() is bus


# ─── DSL v2 Parser ────────────────────────────────────────────────────────────

class TestDSLParser:
    def _parser(self):
        from rebuild.domain.dsl_v2 import DSLParser
        return DSLParser()

    def test_parse_walk(self):
        from rebuild.domain.dsl_v2 import WalkDSL
        model = self._parser().parse("walk repo:/my/app days:7 deploy:none")
        assert isinstance(model, WalkDSL)
        assert model.repo == "/my/app"
        assert model.days == 7
        assert model.deploy == "none"

    def test_parse_walk_dry_run_flag(self):
        from rebuild.domain.dsl_v2 import WalkDSL
        model = self._parser().parse("walk repo:/app dry-run")
        assert model.dry_run is True

    def test_parse_analyze(self):
        from rebuild.domain.dsl_v2 import AnalyzeDSL
        model = self._parser().parse("analyze repo:/app type:duplicates min-lines:4")
        assert isinstance(model, AnalyzeDSL)
        assert model.min_lines == 4

    def test_parse_snapshot(self):
        from rebuild.domain.dsl_v2 import SnapshotDSL
        model = self._parser().parse("snapshot dir:/snaps db:sqlite")
        assert isinstance(model, SnapshotDSL)
        assert model.db == "sqlite"

    def test_parse_prune(self):
        from rebuild.domain.dsl_v2 import PruneDSL
        model = self._parser().parse("prune dir:/snaps keep:3")
        assert isinstance(model, PruneDSL)
        assert model.keep == 3

    def test_unknown_command_raises(self):
        from rebuild.domain.dsl_v2 import DSLParseError
        with pytest.raises(DSLParseError, match="Unknown command"):
            self._parser().parse("deploy repo:/app")

    def test_empty_raises(self):
        from rebuild.domain.dsl_v2 import DSLParseError
        with pytest.raises(DSLParseError):
            self._parser().parse("   ")

    def test_to_cqrs_walk_command(self, tmp_path):
        (tmp_path / ".git").mkdir()
        from rebuild.application.commands.walk_commands import WalkCommand
        cmd = self._parser().to_cqrs_command(f"walk repo:{tmp_path} days:3 deploy:none")
        assert isinstance(cmd, WalkCommand)
        assert cmd.days == 3

    def test_to_cqrs_analyze_command(self, tmp_path):
        from rebuild.application.commands.analyze_commands import AnalyzeCommand
        cmd = self._parser().to_cqrs_command(f"analyze repo:{tmp_path} type:services")
        assert isinstance(cmd, AnalyzeCommand)
        assert cmd.analysis_type == "services"

    def test_to_cqrs_snapshot_command(self, tmp_path):
        from rebuild.application.commands.snapshot_commands import CreateSnapshotCommand
        cmd = self._parser().to_cqrs_command(f"snapshot dir:{tmp_path} db:sqlite")
        assert isinstance(cmd, CreateSnapshotCommand)

    def test_to_cqrs_prune_command(self, tmp_path):
        from rebuild.application.commands.snapshot_commands import PruneSnapshotsCommand
        cmd = self._parser().to_cqrs_command(f"prune dir:{tmp_path} keep:2")
        assert isinstance(cmd, PruneSnapshotsCommand)
        assert cmd.keep == 2

    def test_plugins_returns_none(self, tmp_path):
        cmd = self._parser().to_cqrs_command("plugins")
        assert cmd is None

    def test_history_returns_none(self, tmp_path):
        cmd = self._parser().to_cqrs_command("history dir:.rebuild")
        assert cmd is None

    def test_equals_separator(self):
        from rebuild.domain.dsl_v2 import WalkDSL
        model = self._parser().parse("walk repo=/app days=14")
        assert isinstance(model, WalkDSL)
        assert model.days == 14

    def test_float_threshold(self):
        from rebuild.domain.dsl_v2 import AnalyzeDSL
        model = self._parser().parse("analyze repo:/app type:duplicates threshold:0.9")
        assert model.threshold == pytest.approx(0.9)

    def test_validation_error_on_bad_days(self):
        from rebuild.domain.dsl_v2 import DSLParseError
        with pytest.raises(DSLParseError, match="DSL validation error"):
            self._parser().parse("walk repo:/app days:-1")


# ─── NLP Mapper ────────────────────────────────────────────────────────────────

class TestNLPMapper:
    def _nlp(self):
        from rebuild.domain.dsl_v2 import NLPMapper
        return NLPMapper()

    def test_english_walk(self):
        result = self._nlp().to_dsl("walk /my/repo for the last 7 days")
        assert "walk" in result
        assert "7" in result

    def test_english_analyze_duplicates(self):
        result = self._nlp().to_dsl("analyze duplicates in /my/app")
        assert "analyze" in result
        assert "duplicates" in result

    def test_english_no_deploy(self):
        result = self._nlp().to_dsl("walk /app for the last 5 days without deploying")
        assert "none" in result

    def test_english_dry_run(self):
        result = self._nlp().to_dsl("walk /app dry-run")
        assert "dry-run" in result or "dry_run" in result

    def test_polish_analyze(self):
        result = self._nlp().to_dsl("przeanalizuj duplikaty w /moj/app")
        assert "analyze" in result
        assert "duplicates" in result

    def test_polish_walk(self):
        result = self._nlp().to_dsl("przejdź po repo /app")
        assert "walk" in result

    def test_list_plugins(self):
        result = self._nlp().to_dsl("list plugins")
        assert "plugins" in result

    def test_show_history(self):
        result = self._nlp().to_dsl("show walk history")
        assert "history" in result

    def test_passthrough_for_valid_dsl(self):
        dsl = "walk repo:/app days:7"
        result = self._nlp().to_dsl(dsl)
        assert "walk" in result

    def test_looks_like_dsl(self):
        from rebuild.domain.dsl_v2 import NLPMapper
        nlp = NLPMapper()
        assert nlp._looks_like_dsl("walk repo:/app") is True
        assert nlp._looks_like_dsl("this is natural language") is False


# ─── DSL Shell ────────────────────────────────────────────────────────────────

class TestDSLShell:
    def test_process_line_walk(self, tmp_path):
        (tmp_path / ".git").mkdir()
        from rebuild.domain.dsl_v2 import DSLShell
        from rebuild.application.commands.walk_commands import WalkCommand
        shell = DSLShell(nlp=False)
        cmd = shell.process_line(f"walk repo:{tmp_path} days:3 deploy:none")
        assert isinstance(cmd, WalkCommand)
        assert cmd.days == 3

    def test_process_line_nlp(self):
        from rebuild.domain.dsl_v2 import DSLShell
        shell = DSLShell(nlp=True)
        cmd = shell.process_line("list plugins")
        assert cmd is None  # plugins → query, not command

    def test_process_line_bad_command(self):
        from rebuild.domain.dsl_v2 import DSLShell
        shell = DSLShell(nlp=False)
        cmd = shell.process_line("nonsense xyz abc")
        assert cmd is None

    def test_shell_dispatches_to_bus(self, tmp_path):
        (tmp_path / ".git").mkdir()
        from rebuild.domain.dsl_v2 import DSLShell
        from rebuild.application.commands.base import CommandBus, CommandResult
        from rebuild.application.commands.walk_commands import WalkCommand, WalkCommandResult

        class FakeHandler:
            def handle(self, c):
                return WalkCommandResult(command_id=c.command_id, success=True, total_days=3)

        bus = CommandBus()
        bus.register(WalkCommand, FakeHandler())
        shell = DSLShell(command_bus=bus, nlp=False)
        cmd = shell.process_line(f"walk repo:{tmp_path} days:3 deploy:none")
        assert cmd is not None


# ─── REST API smoke ────────────────────────────────────────────────────────────

class TestAPISmoke:
    def test_create_app_without_fastapi(self):
        """create_app raises ImportError when fastapi not installed."""
        import sys
        # Monkey-patch to simulate missing fastapi
        real_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else None  # type: ignore
        try:
            import fastapi  # noqa: F401
            fastapi_available = True
        except ImportError:
            fastapi_available = False

        if fastapi_available:
            from rebuild.interfaces.api.app import create_app
            app = create_app()
            assert app is not None
            assert app.title == "rebuild API"

    def test_health_endpoint(self):
        try:
            from fastapi.testclient import TestClient
            from rebuild.interfaces.api.app import create_app
        except ImportError:
            pytest.skip("fastapi not installed")

        app = create_app()
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_events_endpoint_no_store(self):
        try:
            from fastapi.testclient import TestClient
            from rebuild.interfaces.api.app import create_app
        except ImportError:
            pytest.skip("fastapi not installed")

        app = create_app()
        client = TestClient(app)
        resp = client.get("/events")
        assert resp.status_code == 200
        assert "events" in resp.json()

    def test_events_endpoint_with_store(self, tmp_path):
        try:
            from fastapi.testclient import TestClient
            from rebuild.interfaces.api.app import create_app
        except ImportError:
            pytest.skip("fastapi not installed")

        from rebuild.infrastructure.event_store import EventStore
        from rebuild.domain.events import WalkStartedEvent
        store = EventStore(tmp_path / "ev.db")
        store.append(WalkStartedEvent(
            aggregate_id="r1", repo="/r", days=7, deploy_method="none"
        ))
        app = create_app(event_store=store)
        client = TestClient(app)
        resp = client.get("/events")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["events"][0]["event_type"] == "WalkStartedEvent"

    def test_commands_dsl_endpoint(self, tmp_path):
        try:
            from fastapi.testclient import TestClient
            from rebuild.interfaces.api.app import create_app
        except ImportError:
            pytest.skip("fastapi not installed")

        (tmp_path / ".git").mkdir()
        from rebuild.application.commands.base import CommandBus
        from rebuild.application.commands.walk_commands import WalkCommand, WalkCommandResult

        class FakeWalkHandler:
            def handle(self, c):
                return WalkCommandResult(
                    command_id=c.command_id, success=True, total_days=7
                )

        bus = CommandBus()
        bus.register(WalkCommand, FakeWalkHandler())
        app = create_app(command_bus=bus)
        client = TestClient(app)
        resp = client.post(
            "/commands/dsl",
            json={"dsl": f"walk repo:{tmp_path} days:7 deploy:none"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_nlp_endpoint(self, tmp_path):
        try:
            from fastapi.testclient import TestClient
            from rebuild.interfaces.api.app import create_app
        except ImportError:
            pytest.skip("fastapi not installed")

        (tmp_path / ".git").mkdir()
        from rebuild.application.commands.base import CommandBus
        from rebuild.application.commands.walk_commands import WalkCommand, WalkCommandResult

        class FakeWalkHandler:
            def handle(self, c):
                return WalkCommandResult(command_id=c.command_id, success=True, total_days=0)

        bus = CommandBus()
        bus.register(WalkCommand, FakeWalkHandler())
        app = create_app(command_bus=bus)
        client = TestClient(app)
        resp = client.post(
            "/commands/nlp",
            json={"text": f"walk {tmp_path} for the last 3 days"},
        )
        assert resp.status_code == 200
