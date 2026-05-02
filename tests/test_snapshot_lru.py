"""
Tests for DBSnapshotManager LRU cache + auto-prune.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.application.services.db_snapshot_manager import DBSnapshotManager, SnapshotInfo


def _make_manager(tmp_path: Path, max_snapshots: int = 5) -> DBSnapshotManager:
    shell = MagicMock()
    shell.run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    mgr = DBSnapshotManager(
        snapshot_dir=tmp_path / "snaps",
        db_container="db",
        db_type="sqlite",
        shell=shell,
        max_snapshots=max_snapshots,
    )
    return mgr


def _inject_snapshot(mgr: DBSnapshotManager, name: str, created_at: str, size: int = 100) -> None:
    """Directly inject a SnapshotInfo without running actual DB commands."""
    sql_file = mgr.snapshot_dir / f"{name}.sql"
    sql_file.write_bytes(b"x" * size)
    mgr._snapshots[name] = SnapshotInfo(
        name=name,
        created_at=created_at,
        size_bytes=size,
        db_type="sqlite",
    )
    mgr._save_metadata()


# ─── stats() ──────────────────────────────────────────────────────────────────

class TestStats:
    def test_empty(self, tmp_path):
        mgr = _make_manager(tmp_path)
        s = mgr.stats()
        assert s["count"] == 0
        assert s["total_size_bytes"] == 0
        assert s["oldest"] is None
        assert s["newest"] is None
        assert s["max_snapshots"] == 5

    def test_with_snapshots(self, tmp_path):
        mgr = _make_manager(tmp_path)
        _inject_snapshot(mgr, "a", "2025-01-01T10:00:00", size=1000)
        _inject_snapshot(mgr, "b", "2025-01-02T10:00:00", size=2000)
        _inject_snapshot(mgr, "c", "2025-01-03T10:00:00", size=500)
        s = mgr.stats()
        assert s["count"] == 3
        assert s["total_size_bytes"] == 3500
        assert s["oldest"] == "2025-01-01T10:00:00"
        assert s["newest"] == "2025-01-03T10:00:00"

    def test_max_snapshots_reflected(self, tmp_path):
        mgr = _make_manager(tmp_path, max_snapshots=3)
        assert mgr.stats()["max_snapshots"] == 3


# ─── prune_old() ──────────────────────────────────────────────────────────────

class TestPruneOld:
    def test_prune_keeps_newest(self, tmp_path):
        mgr = _make_manager(tmp_path, max_snapshots=10)
        for i in range(5):
            _inject_snapshot(mgr, f"snap_{i:02d}", f"2025-01-0{i+1}T00:00:00")
        pruned = mgr.prune_old(keep=3)
        assert pruned == 2
        assert len(mgr._snapshots) == 3
        assert "snap_04" in mgr._snapshots  # newest kept
        assert "snap_03" in mgr._snapshots
        assert "snap_02" in mgr._snapshots

    def test_prune_protects_baseline(self, tmp_path):
        mgr = _make_manager(tmp_path, max_snapshots=10)
        _inject_snapshot(mgr, "baseline", "2025-01-01T00:00:00")
        _inject_snapshot(mgr, "snap_01", "2025-01-02T00:00:00")
        _inject_snapshot(mgr, "snap_02", "2025-01-03T00:00:00")
        pruned = mgr.prune_old(keep=1)
        assert pruned == 1
        assert "baseline" in mgr._snapshots  # never deleted

    def test_prune_protects_baseline_prefix(self, tmp_path):
        mgr = _make_manager(tmp_path, max_snapshots=10)
        _inject_snapshot(mgr, "baseline_abc12345", "2025-01-01T00:00:00")
        _inject_snapshot(mgr, "snap_01", "2025-01-02T00:00:00")
        _inject_snapshot(mgr, "snap_02", "2025-01-03T00:00:00")
        pruned = mgr.prune_old(keep=0)
        assert pruned == 2
        assert "baseline_abc12345" in mgr._snapshots

    def test_prune_nothing_to_delete(self, tmp_path):
        mgr = _make_manager(tmp_path, max_snapshots=10)
        _inject_snapshot(mgr, "snap_01", "2025-01-01T00:00:00")
        pruned = mgr.prune_old(keep=5)
        assert pruned == 0
        assert len(mgr._snapshots) == 1

    def test_prune_uses_max_snapshots_default(self, tmp_path):
        mgr = _make_manager(tmp_path, max_snapshots=2)
        for i in range(5):
            _inject_snapshot(mgr, f"s{i}", f"2025-01-0{i+1}T00:00:00")
        pruned = mgr.prune_old()  # uses max_snapshots=2
        assert pruned == 3
        assert len(mgr._snapshots) == 2

    def test_files_deleted_on_prune(self, tmp_path):
        mgr = _make_manager(tmp_path, max_snapshots=10)
        _inject_snapshot(mgr, "old_snap", "2025-01-01T00:00:00")
        _inject_snapshot(mgr, "new_snap", "2025-01-10T00:00:00")
        mgr.prune_old(keep=1)
        assert not (mgr.snapshot_dir / "old_snap.sql").exists()
        assert (mgr.snapshot_dir / "new_snap.sql").exists()

    def test_metadata_updated_after_prune(self, tmp_path):
        mgr = _make_manager(tmp_path, max_snapshots=10)
        _inject_snapshot(mgr, "s1", "2025-01-01T00:00:00")
        _inject_snapshot(mgr, "s2", "2025-01-02T00:00:00")
        mgr.prune_old(keep=1)
        # Reload from disk
        mgr2 = _make_manager(tmp_path, max_snapshots=10)
        assert "s1" not in mgr2._snapshots
        assert "s2" in mgr2._snapshots


# ─── _auto_prune() ────────────────────────────────────────────────────────────

class TestAutoPrune:
    def test_auto_prune_on_create(self, tmp_path):
        """Creating snapshots beyond max triggers auto-prune."""
        shell = MagicMock()
        shell.run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mgr = DBSnapshotManager(
            snapshot_dir=tmp_path / "snaps",
            db_container="db",
            db_type="sqlite",
            shell=shell,
            max_snapshots=3,
        )
        # Pre-inject 3 snapshots
        for i in range(3):
            _inject_snapshot(mgr, f"old_{i}", f"2025-01-0{i+1}T00:00:00", size=50)

        # Mock the actual dump so create() doesn't shell out
        with patch.object(mgr, "_sqlite_dump", lambda p: p.write_bytes(b"x" * 100)):
            mgr.create("new_snap")

        # Should have pruned 1 old to stay at max=3
        assert len(mgr._snapshots) <= 3
        assert "new_snap" in mgr._snapshots

    def test_auto_prune_disabled_when_zero(self, tmp_path):
        """max_snapshots=0 means no auto-prune."""
        mgr = _make_manager(tmp_path, max_snapshots=0)
        for i in range(20):
            _inject_snapshot(mgr, f"s{i:02d}", f"2025-01-{i+1:02d}T00:00:00")
        pruned = mgr._auto_prune()
        assert pruned == 0
        assert len(mgr._snapshots) == 20

    def test_auto_prune_protects_baseline(self, tmp_path):
        mgr = _make_manager(tmp_path, max_snapshots=2)
        _inject_snapshot(mgr, "baseline", "2025-01-01T00:00:00")
        _inject_snapshot(mgr, "snap_a", "2025-01-02T00:00:00")
        _inject_snapshot(mgr, "snap_b", "2025-01-03T00:00:00")
        # 3 total, max=2 → prune 1 non-baseline
        mgr._auto_prune()
        assert "baseline" in mgr._snapshots


# ─── metadata persistence ─────────────────────────────────────────────────────

class TestMetadataPersistence:
    def test_snapshots_persist_across_instances(self, tmp_path):
        mgr = _make_manager(tmp_path)
        _inject_snapshot(mgr, "snap_x", "2025-06-01T12:00:00", size=512)
        # New instance reads same directory
        mgr2 = _make_manager(tmp_path)
        assert "snap_x" in mgr2._snapshots
        assert mgr2._snapshots["snap_x"].size_bytes == 512

    def test_delete_updates_metadata(self, tmp_path):
        mgr = _make_manager(tmp_path)
        _inject_snapshot(mgr, "to_del", "2025-06-01T12:00:00")
        mgr.delete("to_del")
        mgr2 = _make_manager(tmp_path)
        assert "to_del" not in mgr2._snapshots

    def test_list_snapshots_returns_copy(self, tmp_path):
        mgr = _make_manager(tmp_path)
        _inject_snapshot(mgr, "s1", "2025-01-01T00:00:00")
        listing = mgr.list_snapshots()
        listing["s1"] = None  # mutate copy
        assert mgr._snapshots["s1"] is not None  # original unchanged

    def test_create_baseline_name(self, tmp_path):
        mgr = _make_manager(tmp_path)
        with patch.object(mgr, "_sqlite_dump", lambda p: p.write_bytes(b"x")):
            info = mgr.create_baseline(commit_sha="abc12345def")
        assert info.name == "baseline_abc12345"

    def test_create_baseline_no_sha(self, tmp_path):
        mgr = _make_manager(tmp_path)
        with patch.object(mgr, "_sqlite_dump", lambda p: p.write_bytes(b"x")):
            info = mgr.create_baseline()
        assert info.name == "baseline"
