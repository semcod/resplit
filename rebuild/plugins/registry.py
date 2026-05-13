"""
Plugin registry — discovers and manages rebuild plugins via entry points.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import logging
from typing import Dict, List, Optional, Type, TypeVar

from .base import BaseScanner, BaseReporter

logger = logging.getLogger(__name__)

T = TypeVar("T")

_SCANNER_GROUP = "rebuild.scanners"
_REPORTER_GROUP = "rebuild.reporters"


def _load_entry_points(group: str) -> Dict[str, type]:
    """Load all entry points for *group*, returning {name: class}."""
    loaded: Dict[str, type] = {}
    try:
        eps = importlib.metadata.entry_points(group=group)
    except Exception as exc:
        logger.debug("Could not load entry points for %r: %s", group, exc)
        return loaded

    for ep in eps:
        try:
            cls = ep.load()
            loaded[ep.name] = cls
            logger.debug("Loaded plugin %r from %r", ep.name, group)
        except Exception as exc:
            logger.warning("Failed to load plugin %r from %r: %s", ep.name, group, exc)
    return loaded


class PluginRegistry:
    """
    Central registry for rebuild plugins.

    Usage::

        registry = PluginRegistry()
        registry.discover()

        for name, scanner in registry.scanners.items():
            result = scanner().scan(repo_path)

    Plugins can also be registered programmatically::

        registry.register_scanner("my_scanner", MyScanner)
        registry.register_reporter("my_reporter", MyReporter)
    """

    def __init__(self) -> None:
        self._scanners: Dict[str, Type[BaseScanner]] = {}
        self._reporters: Dict[str, Type[BaseReporter]] = {}
        self._discovered = False

    # ── Discovery ────────────────────────────────────────────────────────────

    def discover(self) -> "PluginRegistry":
        """Load all installed plugins from entry points."""
        scanner_eps = _load_entry_points(_SCANNER_GROUP)
        for name, cls in scanner_eps.items():
            if isinstance(cls, type) and issubclass(cls, BaseScanner):
                self._scanners[name] = cls
            else:
                logger.warning(
                    "Plugin %r in %r is not a BaseScanner subclass", name, _SCANNER_GROUP
                )

        reporter_eps = _load_entry_points(_REPORTER_GROUP)
        for name, cls in reporter_eps.items():
            if isinstance(cls, type) and issubclass(cls, BaseReporter):
                self._reporters[name] = cls
            else:
                logger.warning(
                    "Plugin %r in %r is not a BaseReporter subclass", name, _REPORTER_GROUP
                )

        self._discovered = True
        return self

    # ── Manual registration ───────────────────────────────────────────────────

    def register_scanner(self, name: str, cls: Type[BaseScanner]) -> None:
        """Register a scanner class under *name*."""
        if not (isinstance(cls, type) and issubclass(cls, BaseScanner)):
            raise TypeError(f"{cls!r} must be a subclass of BaseScanner")
        self._scanners[name] = cls

    def register_reporter(self, name: str, cls: Type[BaseReporter]) -> None:
        """Register a reporter class under *name*."""
        if not (isinstance(cls, type) and issubclass(cls, BaseReporter)):
            raise TypeError(f"{cls!r} must be a subclass of BaseReporter")
        self._reporters[name] = cls

    def unregister_scanner(self, name: str) -> None:
        self._scanners.pop(name, None)

    def unregister_reporter(self, name: str) -> None:
        self._reporters.pop(name, None)

    # ── Accessors ─────────────────────────────────────────────────────────────

    @property
    def scanners(self) -> Dict[str, Type[BaseScanner]]:
        return dict(self._scanners)

    @property
    def reporters(self) -> Dict[str, Type[BaseReporter]]:
        return dict(self._reporters)

    def get_scanner(self, name: str) -> Optional[Type[BaseScanner]]:
        return self._scanners.get(name)

    def get_reporter(self, name: str) -> Optional[Type[BaseReporter]]:
        return self._reporters.get(name)

    def scanner_names(self) -> List[str]:
        return sorted(self._scanners)

    def reporter_names(self) -> List[str]:
        return sorted(self._reporters)

    def __repr__(self) -> str:
        return f"PluginRegistry(scanners={self.scanner_names()}, reporters={self.reporter_names()})"


# ── Module-level convenience ──────────────────────────────────────────────────

_default_registry: Optional[PluginRegistry] = None


def load_plugins() -> PluginRegistry:
    """Return the default registry, discovering plugins on first call."""
    global _default_registry
    if _default_registry is None:
        _default_registry = PluginRegistry().discover()
    return _default_registry


def reset_registry() -> None:
    """Reset the default registry (useful in tests)."""
    global _default_registry
    _default_registry = None
