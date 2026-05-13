"""
Base classes for rebuild plugins.

Third-party packages implement these interfaces and register them via
package entry points.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ScanResult:
    """Generic result produced by a scanner plugin."""

    scanner: str
    path: Path
    findings: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseScanner(ABC):
    """
    Base class for rebuild scanner plugins.

    Scanners analyse a repository path and return a list of findings.
    Register via entry point group ``rebuild.scanners``.
    """

    name: str = "unnamed_scanner"
    description: str = ""

    @abstractmethod
    def scan(self, path: Path, **kwargs: Any) -> ScanResult:
        """
        Analyse *path* and return findings.

        Args:
            path: Absolute path to the repository root.
            **kwargs: Optional scanner-specific parameters.

        Returns:
            ScanResult with findings populated.
        """

    def configure(self, config: Dict[str, Any]) -> None:
        """Optional: apply plugin-specific configuration dict."""


class BaseReporter(ABC):
    """
    Base class for rebuild reporter plugins.

    Reporters consume walk/analysis results and produce artefacts
    (files, API calls, notifications, etc.).
    Register via entry point group ``rebuild.reporters``.
    """

    name: str = "unnamed_reporter"
    description: str = ""

    @abstractmethod
    def report(self, results: List[Any], output_dir: Path, **kwargs: Any) -> None:
        """
        Process *results* and write/send output.

        Args:
            results: List of DayResult objects from a walk run.
            output_dir: Directory where artefacts should be written.
            **kwargs: Optional reporter-specific parameters.
        """

    def configure(self, config: Dict[str, Any]) -> None:
        """Optional: apply plugin-specific configuration dict."""
