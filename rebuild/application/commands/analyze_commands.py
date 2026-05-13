"""Analyze-related CQRS Commands."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import Field, field_validator

from .base import Command, CommandResult


class AnalyzeCommand(Command):
    """Trigger codebase analysis."""

    repo: str = Field(..., description="Path to repository")
    analysis_type: str = Field("duplicates", description="duplicates|services|truth|vector-build")
    min_lines: int = Field(6, ge=1)
    semantic: bool = False
    semantic_threshold: float = Field(0.85, ge=0.0, le=1.0)

    @field_validator("analysis_type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        allowed = {"duplicates", "services", "truth", "vector-build", "vector-query", "multi-repo"}
        if v not in allowed:
            raise ValueError(f"analysis_type must be one of {sorted(allowed)}")
        return v


class AnalyzeCommandResult(CommandResult):
    """Result of an AnalyzeCommand."""

    analysis_type: str = ""
    findings_count: int = 0
    summary: str = ""
    details: List[Dict[str, Any]] = Field(default_factory=list)


class NotifyCommand(Command):
    """Send a webhook notification."""

    event: str
    message: str
    severity: str = "info"
    details: Dict[str, Any] = Field(default_factory=dict)
    webhooks: List[Dict[str, Any]] = Field(default_factory=list)


class NotifyCommandResult(CommandResult):
    """Result of a NotifyCommand."""

    sent_count: int = 0
