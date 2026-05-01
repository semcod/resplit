"""Tests for resplit.screenshotter."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from resplit.screenshotter import (
    ScreenshotConfig,
    ScreenshotResult,
    screenshot_endpoint,
    take_screenshot,
    take_screenshots_batch,
)


# ──────────────────────────────────────────────
# take_screenshot
# ──────────────────────────────────────────────

def test_take_screenshot_playwright_not_installed(tmp_path):
    cfg = ScreenshotConfig(output_dir=tmp_path)
    with patch("resplit.screenshotter._playwright_shot", side_effect=ImportError):
        result = take_screenshot("http://localhost/", "test.png", cfg)
    assert result.success is False
    assert "playwright" in result.error.lower()


def test_take_screenshot_success(tmp_path):
    cfg = ScreenshotConfig(output_dir=tmp_path, retries=0)

    def fake_shot(url, path, cfg):
        path.write_bytes(b"PNG")

    with patch("resplit.screenshotter._playwright_shot", side_effect=fake_shot):
        result = take_screenshot("http://localhost/", "test.png", cfg)

    assert result.success is True
    assert result.path == tmp_path / "test.png"
    assert result.attempts == 1


def test_take_screenshot_retry_then_succeed(tmp_path):
    cfg = ScreenshotConfig(output_dir=tmp_path, retries=1, retry_delay_s=0)
    call_count = {"n": 0}

    def fake_shot(url, path, cfg):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("network error")
        path.write_bytes(b"PNG")

    with patch("resplit.screenshotter._playwright_shot", side_effect=fake_shot):
        result = take_screenshot("http://localhost/", "test.png", cfg)

    assert result.success is True
    assert result.attempts == 2


def test_take_screenshot_all_retries_fail(tmp_path):
    cfg = ScreenshotConfig(output_dir=tmp_path, retries=1, retry_delay_s=0)
    with patch("resplit.screenshotter._playwright_shot", side_effect=RuntimeError("fail")):
        result = take_screenshot("http://localhost/", "test.png", cfg)
    assert result.success is False
    assert result.attempts == 2


# ──────────────────────────────────────────────
# screenshot_endpoint
# ──────────────────────────────────────────────

def test_screenshot_endpoint_returns_path_on_success(tmp_path):
    def fake_shot(url, path, cfg):
        path.write_bytes(b"PNG")

    with patch("resplit.screenshotter._playwright_shot", side_effect=fake_shot):
        result = screenshot_endpoint("http://localhost/", "GET_api_health", tmp_path)

    assert result == tmp_path / "GET_api_health.png"


def test_screenshot_endpoint_returns_none_on_failure(tmp_path):
    with patch("resplit.screenshotter._playwright_shot", side_effect=ImportError):
        result = screenshot_endpoint("http://localhost/", "GET_api_health", tmp_path)
    assert result is None


# ──────────────────────────────────────────────
# take_screenshots_batch
# ──────────────────────────────────────────────

def test_take_screenshots_batch_playwright_missing(tmp_path):
    cfg = ScreenshotConfig(output_dir=tmp_path)
    with patch("resplit.screenshotter._batch_playwright", side_effect=ImportError):
        results = take_screenshots_batch([("http://localhost/", "a.png")], cfg)
    assert len(results) == 1
    assert results[0].success is False
