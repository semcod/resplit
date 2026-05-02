"""
CQRS base: Query, QueryResult, QueryHandler, QueryBus.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel, Field


class Query(BaseModel):
    """Base class for all CQRS queries (read side)."""

    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issued_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    class Config:
        arbitrary_types_allowed = True


class QueryResult(BaseModel):
    """Base class for all query results."""

    query_id: str
    success: bool = True
    error: Optional[str] = None


TQuery = TypeVar("TQuery", bound=Query)
TResult = TypeVar("TResult", bound=QueryResult)


class QueryHandler(ABC, Generic[TQuery, TResult]):
    """Handle a single Query type and return a QueryResult."""

    @abstractmethod
    def handle(self, query: TQuery) -> TResult:
        ...


class QueryBus:
    """
    Dispatch Queries to registered handlers.

    Usage::

        bus = QueryBus()
        bus.register(GetWalkHistoryQuery, GetWalkHistoryHandler(history_svc))
        result = bus.dispatch(GetWalkHistoryQuery(results_dir=".rebuild"))
    """

    def __init__(self) -> None:
        self._handlers: Dict[Type[Query], QueryHandler] = {}

    def register(self, query_type: Type[TQuery], handler: QueryHandler) -> None:
        self._handlers[query_type] = handler

    def dispatch(self, query: Query) -> QueryResult:
        handler = self._handlers.get(type(query))
        if handler is None:
            raise ValueError(
                f"No handler registered for {type(query).__name__}"
            )
        return handler.handle(query)
