"""
DeployStrategy protocol: pluggable deployment backends.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class DeployStrategy(Protocol):
    """Protocol for deployment strategies."""

    def start(self, repo: Path) -> bool:
        """Start the service. Returns True on success."""
        ...

    def stop(self, repo: Path) -> None:
        """Stop the service."""
        ...

    @property
    def last_log(self) -> Optional[str]:
        """Last captured deploy log output."""
        ...

    @property
    def last_error_category(self):
        """Last DeployErrorCategory, or None."""
        ...
