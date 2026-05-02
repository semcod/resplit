"""Walk-related CQRS Commands."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from .base import Command, CommandResult


class WalkCommand(Command):
    """Trigger a historical walk of a git repository."""

    repo: str = Field(..., description="Absolute path to the git repository")
    days: int = Field(30, ge=1, le=3650, description="Days of history to walk")
    deploy: str = Field("auto", description="Deploy method: none|docker-compose|auto|custom")
    output: str = Field(".rebuild", description="Output directory")
    health_url: str = Field("http://localhost:8000/health")
    base_url: str = Field("http://localhost:8000")
    screenshots: bool = False
    dry_run: bool = False
    replay: bool = False
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    service: Optional[str] = None
    health_timeout: int = Field(60, ge=1)
    patch_dir: Optional[str] = None
    notifications: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("deploy")
    @classmethod
    def _validate_deploy(cls, v: str) -> str:
        allowed = {"none", "docker-compose", "auto", "custom"}
        if v not in allowed:
            raise ValueError(f"deploy must be one of {sorted(allowed)}")
        return v

    @field_validator("repo")
    @classmethod
    def _validate_repo(cls, v: str) -> str:
        p = Path(v)
        if p.exists() and not (p / ".git").exists():
            raise ValueError(f"{v} is not a git repository")
        return v


class WalkCommandResult(CommandResult):
    """Result of a WalkCommand."""

    total_days: int = 0
    healthy_days: int = 0
    avg_health_pct: float = 0.0
    output_dir: str = ""
