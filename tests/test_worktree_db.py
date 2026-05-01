"""
Coverage tests for worktree_manager and db_snapshot_manager.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.application.services.worktree_manager import WorktreeManager, WorktreeInfo


def _mock_shell(returncode=0, stdout="", stderr=""):
    shell = MagicMock()
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    shell.run.return_value = result
    return shell


# ─────────────────────────────────────────────────────────────
# WorktreeManager
# ─────────────────────────────────────────────────────────────

def test_worktree_path_deterministic(tmp_path):
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=_mock_shell())
    p1 = mgr._worktree_path("abc123def456")
    p2 = mgr._worktree_path("abc123def456")
    assert p1 == p2
    assert "abc123def456" in str(p1)


def test_worktree_path_uses_short_sha(tmp_path):
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=_mock_shell())
    p = mgr._worktree_path("abc123def456789full")
    assert "abc123def456" in str(p)
    assert "789full" not in str(p)


def test_ensure_base_dir_created(tmp_path):
    base = tmp_path / "deep" / "worktrees"
    mgr = WorktreeManager(tmp_path, base, shell=_mock_shell())
    assert base.exists()


def test_list_worktrees_parses_output(tmp_path):
    shell = _mock_shell(stdout="worktree /repo/wt_abc\nHEAD abc123\nbranch refs/heads/main\n")
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    paths = mgr._list_worktrees()
    assert "/repo/wt_abc" in paths


def test_list_worktrees_returns_empty_on_error(tmp_path):
    shell = _mock_shell(returncode=1, stdout="")
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    assert mgr._list_worktrees() == []


def test_get_or_create_cached(tmp_path):
    shell = _mock_shell()
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    sha = "cafebabe1234"
    info = WorktreeInfo(path=tmp_path / "wt" / "wt_cafebabe1234", commit_sha=sha)
    mgr._worktrees[sha] = info
    result = mgr.get_or_create(sha)
    assert result is info
    shell.run.assert_not_called()


def test_get_or_create_creates_new(tmp_path):
    shell = _mock_shell(returncode=0)
    shell.run.side_effect = [
        MagicMock(returncode=0, stdout="worktree /other\n", stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
    ]
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    sha = "deadbeef1234"
    info = mgr.get_or_create(sha)
    assert info.commit_sha == sha
    assert sha in mgr._worktrees


def test_get_or_create_already_in_git(tmp_path):
    sha = "deadbeef1234"
    wt_path = str(tmp_path / "wt" / f"wt_{sha[:12]}")
    shell = _mock_shell(stdout=f"worktree {wt_path}\nHEAD abc\n")
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    info = mgr.get_or_create(sha)
    assert info.commit_sha == sha


def test_remove_worktree(tmp_path):
    shell = _mock_shell()
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    sha = "abc123"
    mgr._worktrees[sha] = WorktreeInfo(path=tmp_path, commit_sha=sha)
    mgr._remove_worktree(sha)
    assert sha not in mgr._worktrees
    shell.run.assert_called()


def test_remove_worktree_force(tmp_path):
    shell = _mock_shell()
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    sha = "abc123"
    mgr._worktrees[sha] = WorktreeInfo(path=tmp_path, commit_sha=sha)
    mgr._remove_worktree(sha, force=True)
    call_args = shell.run.call_args[0][0]
    assert "--force" in call_args


def test_cleanup_all_removes_all(tmp_path):
    shell = _mock_shell()
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    for sha in ["s1", "s2", "s3"]:
        mgr._worktrees[sha] = WorktreeInfo(path=tmp_path, commit_sha=sha)
    mgr.cleanup_all()
    assert mgr._worktrees == {}


def test_cleanup_all_keeps_specified(tmp_path):
    shell = _mock_shell()
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    for sha in ["s1", "s2", "s3"]:
        mgr._worktrees[sha] = WorktreeInfo(path=tmp_path, commit_sha=sha)
    mgr.cleanup_all(keep_shas=["s2"])
    assert "s2" in mgr._worktrees


def test_prepare_sequence(tmp_path):
    sha = "deadbeef1234"
    wt_path = str(tmp_path / "wt" / f"wt_{sha[:12]}")
    shell = _mock_shell(stdout=f"worktree {wt_path}\n")
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    result = mgr.prepare_sequence([sha])
    assert sha in result


def test_get_active_path(tmp_path):
    sha = "abc123456789"
    wt_path = str(tmp_path / "wt" / f"wt_{sha[:12]}")
    shell = _mock_shell(stdout=f"worktree {wt_path}\n")
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    path = mgr.get_active_path(sha)
    assert isinstance(path, Path)


def test_get_or_create_raises_on_failure(tmp_path):
    shell = MagicMock()
    shell.run.side_effect = [
        MagicMock(returncode=0, stdout="worktree /other\n", stderr=""),
        MagicMock(returncode=1, stdout="", stderr="git error"),
    ]
    mgr = WorktreeManager(tmp_path, tmp_path / "wt", shell=shell)
    with pytest.raises(RuntimeError, match="Failed to create worktree"):
        mgr.get_or_create("badf00d12345")


# ─────────────────────────────────────────────────────────────
# db_snapshot_manager — pure logic paths
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.db_snapshot_manager import DBSnapshotManager


def _mgr(tmp_path, db_type="postgres", **kw):
    return DBSnapshotManager(tmp_path, db_container="db", db_type=db_type, **kw)


def test_snapshot_manager_init(tmp_path):
    mgr = _mgr(tmp_path)
    assert mgr.snapshot_dir == tmp_path
    assert mgr.db_container == "db"
    assert mgr.db_type == "postgres"


def test_list_snapshots_empty(tmp_path):
    mgr = _mgr(tmp_path)
    snaps = mgr.list_snapshots()
    assert isinstance(snaps, dict)
    assert snaps == {}


def test_delete_nonexistent_snapshot_returns_true(tmp_path):
    mgr = _mgr(tmp_path)
    result = mgr.delete("nosuch")
    assert result is True


def test_delete_existing_snapshot(tmp_path):
    mgr = _mgr(tmp_path)
    snap_file = tmp_path / "mysnap.sql"
    snap_file.touch()
    from rebuild.application.services.db_snapshot_manager import SnapshotInfo
    import datetime
    mgr._snapshots["mysnap"] = SnapshotInfo(
        name="mysnap",
        created_at=datetime.datetime.now().isoformat(),
        commit_sha=None, size_bytes=0
    )
    result = mgr.delete("mysnap")
    assert result is True
    assert "mysnap" not in mgr._snapshots


def test_ready_check_command_postgres(tmp_path):
    mgr = _mgr(tmp_path, db_type="postgres")
    cmd = mgr._ready_check_command()
    assert isinstance(cmd, list)
    assert any("postgres" in str(c) or "pg_isready" in str(c) for c in cmd)


def test_ready_check_command_mysql(tmp_path):
    mgr = _mgr(tmp_path, db_type="mysql")
    cmd = mgr._ready_check_command()
    assert isinstance(cmd, list)


def test_execute_unknown_action_raises(tmp_path):
    mgr = _mgr(tmp_path)
    with pytest.raises(ValueError, match="Unknown action"):
        mgr.execute("unknown_action")
