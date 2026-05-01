from __future__ import annotations
from typing import Generic, TypeVar, Protocol

TIn = TypeVar("TIn", contravariant=True)
TOut = TypeVar("TOut", covariant=True)

class Service(Protocol, Generic[TIn, TOut]):
    """Standard interface for all application services."""
    def execute(self, input: TIn) -> TOut:
        ...
