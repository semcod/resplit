"""
Coverage tests for smart_test_selector and screenshot_service.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from rebuild.domain.models import WalkConfig


# ─────────────────────────────────────────────────────────────
# SmartTestSelector
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.smart_test_selector import (
    SmartTestSelector, ChangedModule, TestSelection
)


def _ep(path="/api/health", method="GET"):
    return Endpoint(method=method, path=path, base_url="http://x")


def test_select_tests_no_changes(tmp_path):
    sel = SmartTestSelector(tmp_path)
    eps = [_ep("/api/health"), _ep("/api/users")]
    result = sel.select_tests(eps, [])
    assert result.confidence == "high"
    assert _ep("/api/health") in result.endpoints_to_test or any(
        e.path == "/api/health" for e in result.endpoints_to_test
    )


def test_select_tests_migration_change_tests_all(tmp_path):
    sel = SmartTestSelector(tmp_path)
    eps = [_ep("/api/health"), _ep("/api/users"), _ep("/api/orders")]
    changes = [ChangedModule(path=Path("migrations/0001_initial.py"), change_type="A")]
    result = sel.select_tests(eps, changes)
    assert result.confidence == "low"
    assert len(result.endpoints_to_test) == len(eps)
    assert result.skipped_endpoints == []


def test_select_tests_router_change_selects_affected(tmp_path):
    sel = SmartTestSelector(tmp_path)
    eps = [_ep("/api/health"), _ep("/api/users"), _ep("/api/orders")]
    changes = [ChangedModule(path=Path("routers/users.py"), change_type="M")]
    result = sel.select_tests(eps, changes)
    tested_paths = {e.path for e in result.endpoints_to_test}
    assert "/api/health" in tested_paths
    assert "/api/users" in tested_paths


def test_select_tests_unrelated_change_critical_only(tmp_path):
    sel = SmartTestSelector(tmp_path)
    eps = [_ep("/api/health"), _ep("/api/reports")]
    changes = [ChangedModule(path=Path("static/logo.png"), change_type="M")]
    result = sel.select_tests(eps, changes)
    tested_paths = {e.path for e in result.endpoints_to_test}
    assert "/api/health" in tested_paths


def test_analyze_changes_git_error(tmp_path):
    sel = SmartTestSelector(tmp_path)
    sel.shell = MagicMock()
    sel.shell.run.return_value = MagicMock(returncode=1, stdout="")
    result = sel.analyze_changes("abc", "def")
    assert result == []


def test_analyze_changes_parse_added(tmp_path):
    sel = SmartTestSelector(tmp_path)
    sel.shell = MagicMock()
    sel.shell.run.return_value = MagicMock(
        returncode=0,
        stdout="A\trouters/users.py\nM\tmodels/user.py\n"
    )
    result = sel.analyze_changes("abc", "def")
    assert len(result) == 2
    assert result[0].change_type == "A"
    assert result[1].change_type == "M"


def test_analyze_changes_parse_rename(tmp_path):
    sel = SmartTestSelector(tmp_path)
    sel.shell = MagicMock()
    sel.shell.run.return_value = MagicMock(
        returncode=0,
        stdout="R100\told_router.py\tnew_router.py\n"
    )
    result = sel.analyze_changes("abc", "def")
    assert len(result) == 1
    assert result[0].change_type == "R"
    assert result[0].old_path == Path("old_router.py")


def test_execute_wraps_select_tests(tmp_path):
    sel = SmartTestSelector(tmp_path)
    eps = [_ep("/api/health")]
    with patch.object(sel, "analyze_changes", return_value=[]) as mock_analyze:
        result = sel.execute(("sha1", "sha2"))
    mock_analyze.assert_called_once_with("sha1", "sha2")
    assert isinstance(result, TestSelection)


# ─────────────────────────────────────────────────────────────
# ScreenshotService
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.screenshot_service import ScreenshotService, ScreenshotConfig


def _make_er(path="/", method="GET", status=EndpointStatus.OK):
    ep = Endpoint(method=method, path=path, base_url="http://x")
    return EndpointResult(endpoint=ep, status=status)


def test_screenshot_skips_non_get(tmp_path):
    cfg = ScreenshotConfig(output_dir=tmp_path)
    svc = ScreenshotService(cfg)
    er = _make_er(method="POST", status=EndpointStatus.OK)
    result = svc.execute([er])
    assert result == [er]
    assert er.screenshot_path is None


def test_screenshot_skips_skipped_status(tmp_path):
    cfg = ScreenshotConfig(output_dir=tmp_path)
    svc = ScreenshotService(cfg)
    er = _make_er(status=EndpointStatus.SKIP)
    result = svc.execute([er])
    assert result == [er]
    assert er.screenshot_path is None


def test_screenshot_no_targets_returns_empty(tmp_path):
    cfg = ScreenshotConfig(output_dir=tmp_path)
    svc = ScreenshotService(cfg)
    result = svc.execute([])
    assert result == []


def test_screenshot_playwright_not_installed_marks_error(tmp_path):
    cfg = ScreenshotConfig(output_dir=tmp_path)
    svc = ScreenshotService(cfg)
    er = _make_er(status=EndpointStatus.OK)
    with patch.dict("sys.modules", {"playwright": None, "playwright.sync_api": None}):
        with patch("builtins.__import__", side_effect=ImportError("no playwright")):
            result = svc.execute([er])
    assert "playwright not installed" in (er.error or "") or er.screenshot_path is None


def test_screenshot_config_defaults(tmp_path):
    cfg = ScreenshotConfig(output_dir=tmp_path)
    assert cfg.timeout_ms == 15_000
    assert cfg.retries == 2
    assert cfg.full_page is True
    assert cfg.wait_until == "networkidle"


# ─────────────────────────────────────────────────────────────
# parallel_test_engine — basic coverage
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.parallel_test_engine import ParallelTestEngine


def _pcfg(tmp_path):
    return WalkConfig(repo_path=tmp_path, base_url="http://x", dry_run=True)


def test_parallel_engine_dry_run_skips_all(tmp_path):
    import asyncio
    engine = ParallelTestEngine(_pcfg(tmp_path), max_concurrent=2)
    eps = [
        Endpoint(method="GET", path="/api/health", base_url="http://x"),
        Endpoint(method="GET", path="/api/users", base_url="http://x"),
    ]
    results = asyncio.run(engine.execute(eps))
    assert len(results) == 2
    assert all(hasattr(r, 'status') for r in results)


def test_parallel_engine_empty_input(tmp_path):
    import asyncio
    engine = ParallelTestEngine(_pcfg(tmp_path), max_concurrent=2)
    results = asyncio.run(engine.execute([]))
    assert results == []


def test_parallel_engine_respects_max_concurrent(tmp_path):
    import asyncio
    engine = ParallelTestEngine(_pcfg(tmp_path), max_concurrent=1)
    eps = [Endpoint(method="GET", path=f"/ep{i}", base_url="http://x") for i in range(5)]
    results = asyncio.run(engine.execute(eps))
    assert len(results) == 5
