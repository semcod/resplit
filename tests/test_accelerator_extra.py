"""
Targeted coverage for AcceleratorDeployService and parallel_test_engine edge cases.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.domain.models import WalkConfig, DeployMethod
from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus


# ─────────────────────────────────────────────────────────────
# AcceleratorDeployService
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.accelerator_deploy import AcceleratorDeployService
from rebuild.application.services.worktree_manager import WorktreeManager, WorktreeInfo


def _mock_worktrees(tmp_path):
    wm = MagicMock(spec=WorktreeManager)
    wm.get_or_create.return_value = WorktreeInfo(
        path=tmp_path / "wt_abc", commit_sha="abc123"
    )
    return wm


def _cfg(tmp_path, method=DeployMethod.NONE, **kw):
    return WalkConfig(repo_path=tmp_path, deploy_method=method, **kw)


def test_accelerator_start_dry_run(tmp_path):
    cfg = _cfg(tmp_path, dry_run=True)
    svc = AcceleratorDeployService(cfg, _mock_worktrees(tmp_path))
    result = svc.start(tmp_path)
    assert result is True


def test_accelerator_start_deploy_none(tmp_path):
    cfg = _cfg(tmp_path, method=DeployMethod.NONE)
    svc = AcceleratorDeployService(cfg, _mock_worktrees(tmp_path))
    result = svc.start(tmp_path)
    assert result is True


def test_accelerator_stop_dry_run(tmp_path):
    cfg = _cfg(tmp_path, dry_run=True)
    svc = AcceleratorDeployService(cfg, _mock_worktrees(tmp_path))
    svc.stop(tmp_path)


def test_accelerator_project_name_set(tmp_path):
    cfg = _cfg(tmp_path)
    svc = AcceleratorDeployService(cfg, _mock_worktrees(tmp_path))
    assert svc._project_name is not None
    assert len(svc._project_name) > 0


def test_accelerator_volume_name_includes_project(tmp_path):
    cfg = _cfg(tmp_path)
    svc = AcceleratorDeployService(cfg, _mock_worktrees(tmp_path))
    assert svc._project_name in svc._volume_name


def test_accelerator_initial_setup_false(tmp_path):
    cfg = _cfg(tmp_path)
    svc = AcceleratorDeployService(cfg, _mock_worktrees(tmp_path))
    assert svc._initial_setup_done is False


# ─────────────────────────────────────────────────────────────
# parallel_test_engine — with mocked HTTP
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.parallel_test_engine import ParallelTestEngine


def _pcfg(tmp_path, **kw):
    return WalkConfig(repo_path=tmp_path, base_url="http://x", **kw)


def test_parallel_engine_max_concurrent_attribute(tmp_path):
    engine = ParallelTestEngine(_pcfg(tmp_path), max_concurrent=4)
    assert engine.max_concurrent == 4


def test_parallel_engine_open_close_session(tmp_path):
    engine = ParallelTestEngine(_pcfg(tmp_path), max_concurrent=2)
    engine.open_session()
    engine.close_session()


def test_parallel_engine_is_health_endpoint(tmp_path):
    engine = ParallelTestEngine(_pcfg(tmp_path), max_concurrent=2)
    ep_health = Endpoint(method="GET", path="/api/health", base_url="http://x")
    ep_other = Endpoint(method="GET", path="/api/users", base_url="http://x")
    assert engine._is_health_endpoint(ep_health) is True
    assert engine._is_health_endpoint(ep_other) is False


def test_parallel_engine_set_day_dir(tmp_path):
    engine = ParallelTestEngine(_pcfg(tmp_path), max_concurrent=2)
    engine.set_day_dir(tmp_path / "2025-01-01")
    assert engine.day_dir == tmp_path / "2025-01-01"


def test_parallel_engine_multiple_endpoints(tmp_path):
    cfg = _pcfg(tmp_path, dry_run=True)
    engine = ParallelTestEngine(cfg, max_concurrent=3)
    eps = [Endpoint(method="GET", path=f"/ep{i}", base_url="http://x") for i in range(10)]
    results = asyncio.run(engine.execute(eps))
    assert len(results) == 10
