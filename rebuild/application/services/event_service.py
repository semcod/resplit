from __future__ import annotations
import json
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class EventType(Enum):
    """Types of pipeline events for real-time monitoring."""
    PIPELINE_START = "pipeline_start"
    PIPELINE_END = "pipeline_end"
    DAY_START = "day_start"
    DAY_END = "day_end"
    DEPLOY_START = "deploy_start"
    DEPLOY_SUCCESS = "deploy_success"
    DEPLOY_FAIL = "deploy_fail"
    TEST_START = "test_start"
    TEST_END = "test_end"
    TEST_RESULT = "test_result"
    HEALTH_CHECK = "health_check"
    ERROR = "error"
    LOG = "log"


@dataclass
class PipelineEvent:
    """A single pipeline event for real-time streaming."""
    event_type: EventType
    timestamp: str
    data: Dict[str, Any]
    day: Optional[str] = None
    commit: Optional[str] = None

    def to_sse(self) -> str:
        """Convert to Server-Sent Events format."""
        event_dict = {
            "type": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "day": self.day,
            "commit": self.commit,
        }
        return f"data: {json.dumps(event_dict)}\n\n"


class EventService:
    """Service for publishing and subscribing to pipeline events in real-time."""

    def __init__(self):
        self._subscribers: List[queue.Queue] = []
        self._lock = threading.Lock()
        self._enabled = False

    def enable(self) -> None:
        """Enable event publishing."""
        self._enabled = True

    def disable(self) -> None:
        """Disable event publishing and clear subscribers."""
        with self._lock:
            self._enabled = False
            self._subscribers.clear()

    def subscribe(self) -> queue.Queue:
        """Subscribe to event stream. Returns a queue for receiving events."""
        q = queue.Queue(maxsize=100)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        """Unsubscribe from event stream."""
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def publish(self, event: PipelineEvent) -> None:
        """Publish event to all subscribers."""
        if not self._enabled:
            return

        with self._lock:
            dead_subscribers = []
            for q in self._subscribers:
                try:
                    q.put_nowait(event.to_sse())
                except queue.Full:
                    dead_subscribers.append(q)

            for q in dead_subscribers:
                self._subscribers.remove(q)

    def emit(self, event_type: EventType, data: Dict[str, Any], day: Optional[str] = None, commit: Optional[str] = None) -> None:
        """Convenience method to emit an event."""
        event = PipelineEvent(
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat() + "Z",
            data=data,
            day=day,
            commit=commit,
        )
        self.publish(event)


# Global singleton instance
_event_service = EventService()


def get_event_service() -> EventService:
    """Get the global event service singleton."""
    return _event_service
