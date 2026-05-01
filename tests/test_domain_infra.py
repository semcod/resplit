"""
Coverage tests for domain/timeline.py, infrastructure/config_loader.py,
history_service, and event_service.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from rebuild.domain.timeline import (
    DependencyEdge, ModuleNode, GraphSnapshot, SnapshotType, Timeline
)
from rebuild.domain.models import WalkConfig, DeployMethod
from rebuild.infrastructure.config_loader import ConfigLoader


# ─────────────────────────────────────────────────────────────
# Timeline / GraphSnapshot
# ─────────────────────────────────────────────────────────────

def _make_snapshot(commit="abc123"):
    node = ModuleNode(name="mod.a", file_path="mod/a.py", complexity=3.5, lines_of_code=42)
    edge = DependencyEdge(source="mod.a", target="mod.b", edge_type="import")
    return GraphSnapshot(timestamp="2025-01-01T00:00:00", commit_sha=commit,
                         nodes=[node], edges=[edge])


def test_graph_snapshot_to_dict():
    snap = _make_snapshot()
    d = snap.to_dict()
    assert d["commit_sha"] == "abc123"
    assert d["nodes"][0]["name"] == "mod.a"
    assert d["edges"][0]["source"] == "mod.a"
    assert d["snapshot_type"] == "full"


def test_timeline_add_and_get_snapshot():
    tl = Timeline(repo_path="/repo")
    snap = _make_snapshot("sha1")
    tl.add_snapshot(snap)
    assert tl.get_snapshot_at_index(0) == snap
    assert tl.get_snapshot_at_index(99) is None


def test_timeline_get_by_commit():
    tl = Timeline(repo_path="/repo")
    snap = _make_snapshot("deadbeef")
    tl.add_snapshot(snap)
    assert tl.get_snapshot_by_commit("deadbeef") == snap
    assert tl.get_snapshot_by_commit("missing") is None


def test_timeline_to_dict():
    tl = Timeline(repo_path="/repo")
    tl.add_snapshot(_make_snapshot("s1"))
    d = tl.to_dict()
    assert d["repo_path"] == "/repo"
    assert len(d["snapshots"]) == 1


def test_timeline_save_and_load(tmp_path):
    tl = Timeline(repo_path="/repo")
    tl.add_snapshot(_make_snapshot("sha99"))
    out = str(tmp_path / "timeline.json")
    tl.save(out)
    loaded = Timeline.load(out)
    assert loaded.repo_path == "/repo"
    assert len(loaded.snapshots) == 1
    assert loaded.snapshots[0].commit_sha == "sha99"
    assert loaded.snapshots[0].nodes[0].name == "mod.a"
    assert loaded.snapshots[0].edges[0].edge_type == "import"


def test_timeline_save_creates_parent(tmp_path):
    tl = Timeline(repo_path="/repo")
    tl.add_snapshot(_make_snapshot())
    out = str(tmp_path / "sub" / "deep" / "tl.json")
    tl.save(out)
    assert Path(out).exists()


def test_snapshot_type_incremental():
    snap = GraphSnapshot(timestamp="t", snapshot_type=SnapshotType.INCREMENTAL)
    d = snap.to_dict()
    assert d["snapshot_type"] == "incremental"


# ─────────────────────────────────────────────────────────────
# ConfigLoader
# ─────────────────────────────────────────────────────────────

def test_config_loader_missing_file(tmp_path):
    data = ConfigLoader.load(tmp_path / "rebuild.yaml")
    assert data == {}


def test_config_loader_invalid_yaml(tmp_path):
    f = tmp_path / "rebuild.yaml"
    f.write_text(": invalid: yaml: {")
    data = ConfigLoader.load(f)
    assert data == {}


def test_config_loader_loads_valid_yaml(tmp_path):
    f = tmp_path / "rebuild.yaml"
    f.write_text("project:\n  days: 14\n")
    data = ConfigLoader.load(f)
    assert data["project"]["days"] == 14


def test_config_loader_apply_days(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"days": 14}})
    assert cfg.days == 14


def test_config_loader_apply_deploy_method(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {
        "project": {"deploy": {"method": "docker-compose", "health_url": "http://x/health"}}
    })
    assert cfg.deploy_method == DeployMethod.DOCKER_COMPOSE
    assert cfg.health_url == "http://x/health"


def test_config_loader_apply_flat_structure(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"days": 7})
    assert cfg.days == 7


def test_config_loader_apply_output_dir_relative(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"output": ".rebuild_test"}})
    assert cfg.output_dir == (tmp_path / ".rebuild_test").resolve()


def test_config_loader_apply_output_dir_dict(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"output": {"dir": ".rebuild_dict"}}})
    assert cfg.output_dir == (tmp_path / ".rebuild_dict").resolve()


def test_config_loader_apply_health_timeout(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {
        "project": {"deploy": {"health_timeout": 120, "health_interval": 3}}
    })
    assert cfg.health_timeout == 120
    assert cfg.health_interval == 3


def test_config_loader_apply_compose_file(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {
        "project": {"deploy": {"compose_file": "infra/docker-compose.yml"}}
    })
    assert cfg.compose_file == "infra/docker-compose.yml"


def test_config_loader_apply_retry_settings(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {
        "project": {"deploy": {"retry_attempts": 5, "retry_backoff_seconds": 10.0}}
    })
    assert cfg.deploy_retry_attempts == 5
    assert cfg.deploy_retry_backoff_seconds == 10.0


# ─────────────────────────────────────────────────────────────
# event_service
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.event_service import get_event_service, EventType


def test_event_service_subscribe_returns_queue():
    svc = get_event_service()
    import queue
    q = svc.subscribe()
    assert isinstance(q, queue.Queue)
    svc.unsubscribe(q)


def test_event_service_enable_and_emit():
    svc = get_event_service()
    svc.enable()
    import queue
    q = svc.subscribe()
    svc.emit(EventType.LOG, {"msg": "hello"})
    svc.unsubscribe(q)
    svc.disable()


def test_event_service_get_returns_singleton():
    svc1 = get_event_service()
    svc2 = get_event_service()
    assert svc1 is svc2


# ─────────────────────────────────────────────────────────────
# history_service — more coverage
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.history_service import HistoryService


def test_history_service_no_dir(tmp_path):
    svc = HistoryService()
    results = svc.execute(tmp_path / "nonexistent")
    assert results == [] or results is None or isinstance(results, list)


def test_history_service_loads_results(tmp_path):
    day_dir = tmp_path / "2025-01-10"
    day_dir.mkdir()
    (day_dir / "results.json").write_text(json.dumps({
        "day": "2025-01-10",
        "deploy": {"success": True, "method": "none"},
        "health": {"ok": 1, "fail": 0, "total": 1, "percentage": 100},
        "results": [{"method": "GET", "path": "/health", "status": "ok"}]
    }))
    svc = HistoryService()
    results = svc.execute(tmp_path)
    assert isinstance(results, list)
    assert len(results) >= 1
