"""
Additional coverage for db_snapshot_manager — pure logic paths
that don't need real docker.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from rebuild.application.services.db_snapshot_manager import DBSnapshotManager, SnapshotInfo


def _shell(returncode=0, stdout="", stderr=""):
    s = MagicMock()
    r = MagicMock()
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    s.run.return_value = r
    return s


def _mgr(tmp_path, db_type="postgres", **kw):
    return DBSnapshotManager(tmp_path, db_container="db", db_type=db_type,
                             shell=_shell(), **kw)


# ─────────────────────────────────────────────────────────────
# _ready_check_command
# ─────────────────────────────────────────────────────────────

def test_ready_check_sqlite(tmp_path):
    mgr = _mgr(tmp_path, db_type="sqlite")
    cmd = mgr._ready_check_command()
    assert cmd == ["true"]


def test_ready_check_postgres_contains_pg_isready(tmp_path):
    mgr = _mgr(tmp_path, db_type="postgres")
    cmd = mgr._ready_check_command()
    assert "pg_isready" in cmd


def test_ready_check_mysql_contains_mysqladmin(tmp_path):
    mgr = _mgr(tmp_path, db_type="mysql")
    cmd = mgr._ready_check_command()
    assert "mysqladmin" in cmd


# ─────────────────────────────────────────────────────────────
# _wait_until_ready
# ─────────────────────────────────────────────────────────────

def test_wait_until_ready_sqlite_immediate(tmp_path):
    mgr = _mgr(tmp_path, db_type="sqlite")
    assert mgr._wait_until_ready() is True


def test_wait_until_ready_postgres_success(tmp_path):
    mgr = _mgr(tmp_path, db_type="postgres", ready_timeout=5, ready_interval=0.01)
    mgr.shell.run.return_value = MagicMock(returncode=0)
    assert mgr._wait_until_ready() is True


def test_wait_until_ready_postgres_timeout(tmp_path):
    mgr = _mgr(tmp_path, db_type="postgres", ready_timeout=0.05, ready_interval=0.01)
    mgr.shell.run.return_value = MagicMock(returncode=1)
    assert mgr._wait_until_ready() is False


# ─────────────────────────────────────────────────────────────
# _save_metadata / _load_metadata
# ─────────────────────────────────────────────────────────────

def test_save_and_load_metadata(tmp_path):
    mgr = _mgr(tmp_path)
    info = SnapshotInfo(
        name="snap1",
        created_at=datetime.datetime.now().isoformat(),
        commit_sha="abc",
        size_bytes=1024,
    )
    mgr._snapshots["snap1"] = info
    mgr._save_metadata()

    mgr2 = DBSnapshotManager(tmp_path, db_container="db", db_type="postgres",
                              shell=_shell())
    assert "snap1" in mgr2._snapshots
    assert mgr2._snapshots["snap1"].commit_sha == "abc"


def test_load_metadata_ignores_corrupt_file(tmp_path):
    (tmp_path / "snapshots.json").write_text("NOT JSON {{{{")
    mgr = DBSnapshotManager(tmp_path, db_container="db", db_type="postgres",
                            shell=_shell())
    assert mgr._snapshots == {}


# ─────────────────────────────────────────────────────────────
# restore — raises when snapshot missing
# ─────────────────────────────────────────────────────────────

def test_restore_raises_if_not_found(tmp_path):
    mgr = _mgr(tmp_path)
    with pytest.raises(ValueError, match="not found"):
        mgr.restore("nosuch")


def test_restore_raises_if_file_missing(tmp_path):
    mgr = _mgr(tmp_path)
    mgr._snapshots["snap"] = SnapshotInfo(
        name="snap", created_at="t", commit_sha=None, size_bytes=0
    )
    with pytest.raises(FileNotFoundError):
        mgr.restore("snap")


# ─────────────────────────────────────────────────────────────
# _mysql_dump
# ─────────────────────────────────────────────────────────────

def test_mysql_dump_success(tmp_path):
    shell = _shell(returncode=0, stdout="-- SQL content --")
    mgr = DBSnapshotManager(tmp_path, db_container="db", db_type="mysql",
                            shell=shell)
    out = tmp_path / "snap.sql"
    mgr._mysql_dump(out)
    assert out.exists()
    assert "SQL content" in out.read_text()


def test_mysql_dump_failure_raises(tmp_path):
    shell = _shell(returncode=1, stderr="mysqldump error")
    mgr = DBSnapshotManager(tmp_path, db_container="db", db_type="mysql",
                            shell=shell)
    with pytest.raises(RuntimeError, match="mysqldump failed"):
        mgr._mysql_dump(tmp_path / "snap.sql")


# ─────────────────────────────────────────────────────────────
# _sqlite_dump
# ─────────────────────────────────────────────────────────────

def test_sqlite_dump_calls_docker_cp(tmp_path):
    shell = _shell()
    mgr = DBSnapshotManager(tmp_path, db_container="mydb", db_type="sqlite",
                            shell=shell)
    mgr._sqlite_dump(tmp_path / "snap.sql")
    shell.run.assert_called_once()
    call_args = shell.run.call_args[0][0]
    assert "docker" in call_args
    assert "cp" in call_args


# ─────────────────────────────────────────────────────────────
# create — unsupported db type
# ─────────────────────────────────────────────────────────────

def test_create_unsupported_db_type(tmp_path):
    mgr = _mgr(tmp_path, db_type="cassandra")
    with pytest.raises(ValueError, match="Unsupported DB type"):
        mgr.create("snap1")


# ─────────────────────────────────────────────────────────────
# execute — baseline
# ─────────────────────────────────────────────────────────────

def test_execute_baseline_calls_create_baseline(tmp_path):
    mgr = _mgr(tmp_path)
    with patch.object(mgr, "create_baseline") as mock_cb:
        mock_cb.return_value = SnapshotInfo(
            name="baseline", created_at="t", commit_sha=None, size_bytes=0
        )
        result = mgr.execute("baseline")
    mock_cb.assert_called_once()
    assert result.name == "baseline"


def test_execute_unknown_raises(tmp_path):
    mgr = _mgr(tmp_path)
    with pytest.raises(ValueError):
        mgr.execute("bad_action")


# ─────────────────────────────────────────────────────────────
# create_baseline
# ─────────────────────────────────────────────────────────────

def test_create_baseline_calls_create(tmp_path):
    mgr = _mgr(tmp_path)
    with patch.object(mgr, "create") as mock_create:
        mock_create.return_value = SnapshotInfo(
            name="baseline", created_at="t", commit_sha=None, size_bytes=0
        )
        result = mgr.create_baseline()
    mock_create.assert_called_once_with("baseline", None)


def test_create_baseline_with_sha_uses_sha_prefix(tmp_path):
    mgr = _mgr(tmp_path)
    with patch.object(mgr, "create") as mock_create:
        mock_create.return_value = SnapshotInfo(
            name="baseline_abcdefgh", created_at="t", commit_sha="abcdefgh12345", size_bytes=0
        )
        result = mgr.create_baseline(commit_sha="abcdefgh12345")
    call_args = mock_create.call_args[0]
    assert call_args[0].startswith("baseline_")
    assert "abcdefgh" in call_args[0]
