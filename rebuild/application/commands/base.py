"""
CQRS base: Command, CommandResult, CommandHandler, CommandBus.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class Command(BaseModel):
    """Base class for all CQRS commands (write side)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    command_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issued_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class CommandResult(BaseModel):
    """Base class for all command results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    command_id: str
    success: bool
    error: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


TCommand = TypeVar("TCommand", bound=Command)
TResult = TypeVar("TResult", bound=CommandResult)


class CommandHandler(ABC, Generic[TCommand, TResult]):
    """Handle a single Command type and return a CommandResult."""

    @abstractmethod
    def handle(self, command: TCommand) -> TResult:
        ...


class CommandBus:
    """
    Dispatch Commands to registered handlers.

    Usage::

        bus = CommandBus()
        bus.register(WalkCommand, WalkCommandHandler())
        result = bus.dispatch(WalkCommand(repo="/my/repo", days=7))
    """

    def __init__(self) -> None:
        self._handlers: Dict[Type[Command], CommandHandler] = {}
        self._middlewares: List[Any] = []

    def register(self, command_type: Type[TCommand], handler: CommandHandler) -> None:
        self._handlers[command_type] = handler

    def dispatch(self, command: Command) -> CommandResult:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise ValueError(
                f"No handler registered for {type(command).__name__}"
            )
        return handler.handle(command)
