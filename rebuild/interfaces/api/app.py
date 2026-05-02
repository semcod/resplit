"""
rebuild REST + WebSocket API.

Endpoints:
  POST /commands/walk          — dispatch WalkCommand
  POST /commands/analyze       — dispatch AnalyzeCommand
  POST /commands/snapshot      — dispatch CreateSnapshotCommand
  POST /commands/prune         — dispatch PruneSnapshotsCommand
  POST /commands/dsl           — parse & dispatch a DSL string
  POST /commands/nlp           — NLP → DSL → Command

  GET  /queries/history        — GetWalkHistoryQuery
  GET  /queries/day/{day}      — GetDayResultQuery
  GET  /queries/snapshots      — GetSnapshotStatsQuery
  GET  /queries/plugins        — GetPluginsQuery

  GET  /events/stream          — SSE stream of all events
  GET  /events                 — paginated event log from EventStore

  WS   /ws/events              — WebSocket real-time event push
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, Optional

from pydantic import BaseModel


def create_app(
    command_bus=None,
    query_bus=None,
    event_store=None,
    event_bus=None,
):
    """
    Create and return a FastAPI application.

    All dependencies are injected — ideal for testing.
    """
    try:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import StreamingResponse
    except ImportError as exc:
        raise ImportError(
            "FastAPI is required for the API server. "
            "Install with: pip install 'rebuild[api]'"
        ) from exc

    from ...application.commands import (
        CommandBus, WalkCommand, AnalyzeCommand,
        CreateSnapshotCommand, PruneSnapshotsCommand,
    )
    from ...application.queries import (
        QueryBus, GetWalkHistoryQuery, GetDayResultQuery,
        GetSnapshotStatsQuery, GetPluginsQuery,
    )
    from ...infrastructure.event_bus import EventBus, get_event_bus
    from ...domain.dsl_v2 import DSLParser, NLPMapper

    _command_bus: CommandBus = command_bus or CommandBus()
    _query_bus: QueryBus = query_bus or QueryBus()
    _event_bus: EventBus = event_bus or get_event_bus()
    _event_store = event_store

    app = FastAPI(
        title="rebuild API",
        description="CQRS/ES REST + WebSocket API for rebuild.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Commands ─────────────────────────────────────────────────────────────

    @app.post("/commands/walk", tags=["commands"])
    async def cmd_walk(cmd: WalkCommand) -> Dict[str, Any]:
        result = _command_bus.dispatch(cmd)
        return result.model_dump()

    @app.post("/commands/analyze", tags=["commands"])
    async def cmd_analyze(cmd: AnalyzeCommand) -> Dict[str, Any]:
        result = _command_bus.dispatch(cmd)
        return result.model_dump()

    @app.post("/commands/snapshot", tags=["commands"])
    async def cmd_snapshot(cmd: CreateSnapshotCommand) -> Dict[str, Any]:
        result = _command_bus.dispatch(cmd)
        return result.model_dump()

    @app.post("/commands/prune", tags=["commands"])
    async def cmd_prune(cmd: PruneSnapshotsCommand) -> Dict[str, Any]:
        result = _command_bus.dispatch(cmd)
        return result.model_dump()

    class DSLRequest(BaseModel):
        dsl: str

    class NLPRequest(BaseModel):
        text: str

    @app.post("/commands/dsl", tags=["commands"])
    async def cmd_dsl(req: DSLRequest) -> Dict[str, Any]:
        """Parse a DSL string and dispatch the resulting command."""
        parser = DSLParser()
        cmd = parser.to_cqrs_command(req.dsl)
        if cmd is None:
            return {"error": "Could not parse DSL", "dsl": req.dsl}
        result = _command_bus.dispatch(cmd)
        return result.model_dump()

    @app.post("/commands/nlp", tags=["commands"])
    async def cmd_nlp(req: NLPRequest) -> Dict[str, Any]:
        """Map natural language to DSL, then dispatch the command."""
        mapper = NLPMapper()
        dsl_str = mapper.to_dsl(req.text)
        if not dsl_str:
            return {"error": "Could not interpret request", "text": req.text}
        parser = DSLParser()
        cmd = parser.to_cqrs_command(dsl_str)
        if cmd is None:
            return {"error": "DSL parse failed", "dsl": dsl_str}
        result = _command_bus.dispatch(cmd)
        return {**result.model_dump(), "dsl": dsl_str}

    # ─── Queries ──────────────────────────────────────────────────────────────

    @app.get("/queries/history", tags=["queries"])
    async def qry_history(
        results_dir: str = ".rebuild",
        limit: int = 100,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        q = GetWalkHistoryQuery(
            results_dir=results_dir, limit=limit,
            date_from=date_from, date_to=date_to,
        )
        result = _query_bus.dispatch(q)
        return result.model_dump()

    @app.get("/queries/day/{day}", tags=["queries"])
    async def qry_day(day: str, results_dir: str = ".rebuild") -> Dict[str, Any]:
        q = GetDayResultQuery(results_dir=results_dir, day=day)
        result = _query_bus.dispatch(q)
        return result.model_dump()

    @app.get("/queries/snapshots", tags=["queries"])
    async def qry_snapshots(snapshot_dir: str) -> Dict[str, Any]:
        q = GetSnapshotStatsQuery(snapshot_dir=snapshot_dir)
        result = _query_bus.dispatch(q)
        return result.model_dump()

    @app.get("/queries/plugins", tags=["queries"])
    async def qry_plugins(group: Optional[str] = None) -> Dict[str, Any]:
        q = GetPluginsQuery(group=group)
        result = _query_bus.dispatch(q)
        return result.model_dump()

    # ─── Events (SSE) ─────────────────────────────────────────────────────────

    @app.get("/events", tags=["events"])
    async def events_log(
        aggregate_id: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 200,
    ) -> Dict[str, Any]:
        if _event_store is None:
            return {"events": [], "error": "No EventStore configured"}
        rows = _event_store.load_raw(
            aggregate_id=aggregate_id,
            event_type=event_type,
            since=since,
            limit=limit,
        )
        return {"events": rows, "total": len(rows)}

    @app.get("/events/stream", tags=["events"])
    async def events_sse() -> StreamingResponse:
        """Server-Sent Events stream of all live domain events."""
        queue = _event_bus.create_ws_queue(maxsize=512)

        async def generator() -> AsyncGenerator[str, None]:
            try:
                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=30.0)
                        data = json.dumps(event.to_dict())
                        yield f"data: {data}\n\n"
                    except asyncio.TimeoutError:
                        yield ": keepalive\n\n"
            finally:
                _event_bus.remove_ws_queue(queue)

        return StreamingResponse(generator(), media_type="text/event-stream")

    # ─── WebSocket ────────────────────────────────────────────────────────────

    @app.websocket("/ws/events")
    async def ws_events(websocket: WebSocket) -> None:
        """WebSocket endpoint — push all domain events to connected clients."""
        await websocket.accept()
        queue = _event_bus.create_ws_queue(maxsize=512)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    await websocket.send_text(json.dumps(event.to_dict()))
                except asyncio.TimeoutError:
                    await websocket.send_text(json.dumps({"type": "keepalive"}))
        except WebSocketDisconnect:
            pass
        finally:
            _event_bus.remove_ws_queue(queue)

    # ─── Health ───────────────────────────────────────────────────────────────

    @app.get("/health", tags=["meta"])
    async def health() -> Dict[str, str]:
        return {"status": "ok", "service": "rebuild-api"}

    return app
