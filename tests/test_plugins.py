"""Tests for rebuild.plugins (registry, base, discovery)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, List
from unittest.mock import patch

import pytest

from rebuild.plugins import PluginRegistry, load_plugins
from rebuild.plugins.base import BaseReporter, BaseScanner, ScanResult
from rebuild.plugins.registry import (
    _REPORTER_GROUP,
    _SCANNER_GROUP,
    _load_entry_points,
    reset_registry,
)


# ──────────────────────────────────────────────
# Fixtures: minimal plugin implementations
# ──────────────────────────────────────────────

class _DummyScanner(BaseScanner):
    name = "dummy"
    description = "A dummy test scanner."

    def scan(self, path: Path, **kwargs: Any) -> ScanResult:
        return ScanResult(scanner=self.name, path=path, findings=[{"x": 1}])


class _DummyReporter(BaseReporter):
    name = "dummy_reporter"
    description = "A dummy test reporter."

    def report(self, results: List[Any], output_dir: Path, **kwargs: Any) -> None:
        (output_dir / "report.txt").write_text("ok")


class _NotAScanner:
    """Class that is not a BaseScanner subclass — used to test type rejection."""


# ──────────────────────────────────────────────
# ScanResult dataclass
# ──────────────────────────────────────────────

def test_scan_result_defaults(tmp_path):
    r = ScanResult(scanner="s", path=tmp_path)
    assert r.scanner == "s"
    assert r.path == tmp_path
    assert r.findings == []
    assert r.summary == ""
    assert r.metadata == {}


def test_scan_result_carries_findings(tmp_path):
    r = ScanResult(scanner="s", path=tmp_path, findings=[{"a": 1}], summary="ok",
                   metadata={"v": 1})
    assert r.findings == [{"a": 1}]
    assert r.summary == "ok"
    assert r.metadata == {"v": 1}


# ──────────────────────────────────────────────
# BaseScanner / BaseReporter
# ──────────────────────────────────────────────

def test_base_scanner_is_abstract():
    with pytest.raises(TypeError):
        BaseScanner()  # type: ignore[abstract]


def test_base_reporter_is_abstract():
    with pytest.raises(TypeError):
        BaseReporter()  # type: ignore[abstract]


def test_dummy_scanner_runs(tmp_path):
    s = _DummyScanner()
    r = s.scan(tmp_path)
    assert r.scanner == "dummy"
    assert r.findings == [{"x": 1}]


def test_dummy_reporter_writes_file(tmp_path):
    rep = _DummyReporter()
    rep.report([], tmp_path)
    assert (tmp_path / "report.txt").read_text() == "ok"


def test_configure_default_is_noop():
    """Default configure() implementation must not raise."""
    s = _DummyScanner()
    s.configure({"foo": "bar"})
    rep = _DummyReporter()
    rep.configure({"foo": "bar"})


# ──────────────────────────────────────────────
# PluginRegistry — manual registration
# ──────────────────────────────────────────────

def test_registry_starts_empty():
    reg = PluginRegistry()
    assert reg.scanners == {}
    assert reg.reporters == {}
    assert reg.scanner_names() == []
    assert reg.reporter_names() == []


def test_register_scanner_and_get():
    reg = PluginRegistry()
    reg.register_scanner("dummy", _DummyScanner)
    assert reg.get_scanner("dummy") is _DummyScanner
    assert reg.scanner_names() == ["dummy"]
    assert reg.scanners == {"dummy": _DummyScanner}


def test_register_reporter_and_get():
    reg = PluginRegistry()
    reg.register_reporter("dummy_rep", _DummyReporter)
    assert reg.get_reporter("dummy_rep") is _DummyReporter
    assert reg.reporter_names() == ["dummy_rep"]


def test_register_scanner_rejects_wrong_type():
    reg = PluginRegistry()
    with pytest.raises(TypeError):
        reg.register_scanner("bad", _NotAScanner)  # type: ignore[arg-type]


def test_register_reporter_rejects_wrong_type():
    reg = PluginRegistry()
    with pytest.raises(TypeError):
        reg.register_reporter("bad", _NotAScanner)  # type: ignore[arg-type]


def test_register_scanner_rejects_non_class_instance():
    reg = PluginRegistry()
    with pytest.raises(TypeError):
        reg.register_scanner("bad", _DummyScanner())  # type: ignore[arg-type]


def test_unregister_scanner():
    reg = PluginRegistry()
    reg.register_scanner("dummy", _DummyScanner)
    reg.unregister_scanner("dummy")
    assert reg.get_scanner("dummy") is None
    # Unregistering a missing name is a no-op:
    reg.unregister_scanner("nonexistent")


def test_unregister_reporter():
    reg = PluginRegistry()
    reg.register_reporter("dummy_rep", _DummyReporter)
    reg.unregister_reporter("dummy_rep")
    assert reg.get_reporter("dummy_rep") is None
    reg.unregister_reporter("nonexistent")


def test_get_returns_none_for_missing():
    reg = PluginRegistry()
    assert reg.get_scanner("missing") is None
    assert reg.get_reporter("missing") is None


def test_repr_lists_names():
    reg = PluginRegistry()
    reg.register_scanner("s1", _DummyScanner)
    reg.register_reporter("r1", _DummyReporter)
    text = repr(reg)
    assert "s1" in text and "r1" in text
    assert text.startswith("PluginRegistry(")


def test_scanners_property_returns_copy():
    reg = PluginRegistry()
    reg.register_scanner("s1", _DummyScanner)
    snapshot = reg.scanners
    snapshot["mutated"] = _DummyScanner   # type: ignore[assignment]
    assert "mutated" not in reg.scanners


def test_reporters_property_returns_copy():
    reg = PluginRegistry()
    reg.register_reporter("r1", _DummyReporter)
    snapshot = reg.reporters
    snapshot["mutated"] = _DummyReporter   # type: ignore[assignment]
    assert "mutated" not in reg.reporters


# ──────────────────────────────────────────────
# Discovery via entry points
# ──────────────────────────────────────────────

class _FakeEntryPoint:
    def __init__(self, name: str, target: Any, raise_on_load: bool = False):
        self.name = name
        self._target = target
        self._raise = raise_on_load

    def load(self) -> Any:
        if self._raise:
            raise RuntimeError("simulated load failure")
        return self._target


def test_discover_loads_valid_scanners_and_reporters():
    fake_eps = {
        _SCANNER_GROUP: [_FakeEntryPoint("dummy", _DummyScanner)],
        _REPORTER_GROUP: [_FakeEntryPoint("dummy_rep", _DummyReporter)],
    }

    def fake_entry_points(group: str):
        return fake_eps.get(group, [])

    reg = PluginRegistry()
    with patch("rebuild.plugins.registry.importlib.metadata.entry_points",
               side_effect=fake_entry_points):
        reg.discover()
    assert reg.get_scanner("dummy") is _DummyScanner
    assert reg.get_reporter("dummy_rep") is _DummyReporter


def test_discover_skips_invalid_subclass():
    fake_eps = {
        _SCANNER_GROUP: [_FakeEntryPoint("bad", _NotAScanner)],
        _REPORTER_GROUP: [],
    }
    with patch("rebuild.plugins.registry.importlib.metadata.entry_points",
               side_effect=lambda group: fake_eps.get(group, [])):
        reg = PluginRegistry().discover()
    assert reg.get_scanner("bad") is None


def test_discover_handles_load_failure_gracefully():
    fake_eps = {
        _SCANNER_GROUP: [_FakeEntryPoint("broken", None, raise_on_load=True)],
        _REPORTER_GROUP: [],
    }
    with patch("rebuild.plugins.registry.importlib.metadata.entry_points",
               side_effect=lambda group: fake_eps.get(group, [])):
        reg = PluginRegistry().discover()
    # Discovery must not raise; the broken plugin is simply absent.
    assert reg.get_scanner("broken") is None


def test_load_entry_points_swallows_metadata_errors():
    with patch("rebuild.plugins.registry.importlib.metadata.entry_points",
               side_effect=RuntimeError("boom")):
        result = _load_entry_points("any.group")
    assert result == {}


# ──────────────────────────────────────────────
# Module-level convenience
# ──────────────────────────────────────────────

def test_load_plugins_returns_singleton():
    reset_registry()
    try:
        with patch("rebuild.plugins.registry.importlib.metadata.entry_points",
                   side_effect=lambda group: []):
            r1 = load_plugins()
            r2 = load_plugins()
        assert r1 is r2
    finally:
        reset_registry()


def test_reset_registry_forces_rediscovery():
    with patch("rebuild.plugins.registry.importlib.metadata.entry_points",
               side_effect=lambda group: []):
        r1 = load_plugins()
        reset_registry()
        r2 = load_plugins()
    assert r1 is not r2
    reset_registry()
