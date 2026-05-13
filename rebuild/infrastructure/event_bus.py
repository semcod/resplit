"""
In-process EventBus with async subscriber support.

Subscribers receive DomainEvents synchronously or via asyncio queues (for WS).
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Type

from ..domain.events.domain_events import DomainEvent

logger = logging.getLogger(__name__)

SyncHandler = Callable[[DomainEvent], None]
AsyncHandler = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    """
    Publish/subscribe event bus.

    - Sync subscribers: called immediately on publish()
    - Async subscribers: scheduled in running event loop if present
    - WS queues: asyncio.Queue objects fed on every event (for WebSocket push)

    Usage::

        bus = EventBus()

        # Sync subscriber
        bus.subscribe(WalkFinishedEvent, lambda e: print("Done!", e.total_days))

        # Publish
        bus.publish(WalkFinishedEvent(aggregate_id="r1", total_days=7, ...))

        # WS queue
        q = bus.create_ws_queue()
        # ... in WS handler: event = await q.get()
    """

    def __init__(self, event_store: Optional[Any] = None) -> None:
        self._sync_handlers: Dict[Type[DomainEvent], List[SyncHandler]] = defaultdict(list)
        self._async_handlers: Dict[Type[DomainEvent], List[AsyncHandler]] = defaultdict(list)
        self._global_sync: List[SyncHandler] = []
        self._global_async: List[AsyncHandler] = []
        self._ws_queues: Set[asyncio.Queue] = set()
        self._event_store = event_store

    # ─── Subscribe ────────────────────────────────────────────────────────────

    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: SyncHandler,
    ) -> None:
        self._sync_handlers[event_type].append(handler)

    def subscribe_async(
        self,
        event_type: Type[DomainEvent],
        handler: AsyncHandler,
    ) -> None:
        self._async_handlers[event_type].append(handler)

    def subscribe_all(self, handler: SyncHandler) -> None:
        """Subscribe to every event type."""
        self._global_sync.append(handler)

    def subscribe_all_async(self, handler: AsyncHandler) -> None:
        self._global_async.append(handler)

    def unsubscribe(self, event_type: Type[DomainEvent], handler: SyncHandler) -> None:
        handlers = self._sync_handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    # ─── WS queues ────────────────────────────────────────────────────────────

    def create_ws_queue(self, maxsize: int = 256) -> asyncio.Queue:
        """Create and register a new WS consumer queue."""
        q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._ws_queues.add(q)
        return q

    def remove_ws_queue(self, q: asyncio.Queue) -> None:
        self._ws_queues.discard(q)

    # ─── Publish ──────────────────────────────────────────────────────────────

    def publish(self, event: DomainEvent) -> None:
        """Publish event — dispatch to all registered handlers."""
        # Persist to EventStore if configured
        if self._event_store is not None:
            try:
                self._event_store.append(event)
            except Exception as exc:
                logger.warning("EventStore append failed: %s", exc)

        # Typed sync handlers
        for handler in self._sync_handlers.get(type(event), []):
            try:
                handler(event)
            except Exception as exc:
                logger.error("Sync handler %r raised: %s", handler, exc)

        # Global sync handlers
        for handler in self._global_sync:
            try:
                handler(event)
            except Exception as exc:
                logger.error("Global sync handler %r raised: %s", handler, exc)

        # Push to WS queues (non-blocking)
        dead: Set[asyncio.Queue] = set()
        for q in list(self._ws_queues):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.debug("WS queue full, dropping event %s", event.event_type)
            except Exception:
                dead.add(q)
        self._ws_queues -= dead

        # Schedule async handlers if a loop is running
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None:
            for handler in self._async_handlers.get(type(event), []):
                loop.create_task(handler(event))
            for handler in self._global_async:
                loop.create_task(handler(event))

    def publish_many(self, events: List[DomainEvent]) -> None:
        for event in events:
            self.publish(event)

    @property
    def ws_queue_count(self) -> int:
        return len(self._ws_queues)


# Singleton for the application (can be overridden in tests)
_default_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus


def set_event_bus(bus: EventBus) -> None:
    global _default_bus
    _default_bus = bus
