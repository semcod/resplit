"""
rebuild.screenshotter — Playwright screenshots per endpoint z retry/timeout.

Używany przez cli.py walk jako osobny moduł (nie inline w cli).
Playwright jest opcjonalny — brak instalacji → graceful skip.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ──────────────────────────────────────────────
# Konfiguracja
# ──────────────────────────────────────────────

@dataclass
class ScreenshotConfig:
    output_dir: Path
    timeout_ms: int = 15_000
    retries: int = 2
    retry_delay_s: float = 1.0
    full_page: bool = True
    wait_until: str = "networkidle"   # networkidle | load | domcontentloaded


@dataclass
class ScreenshotResult:
    url: str
    path: Optional[Path] = None
    success: bool = False
    error: Optional[str] = None
    attempts: int = 0
    duration_ms: float = 0.0


# ──────────────────────────────────────────────
# Główny entry point
# ──────────────────────────────────────────────

def take_screenshot(url: str, filename: str, cfg: ScreenshotConfig) -> ScreenshotResult:
    """
    Robi screenshot URL i zapisuje do cfg.output_dir/filename.

    Retries: cfg.retries prób z cfg.retry_delay_s przerwą.
    Zwraca ScreenshotResult niezależnie od tego czy się powiodło.
    """
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.output_dir / filename

    result = ScreenshotResult(url=url)

    for attempt in range(1, cfg.retries + 2):
        result.attempts = attempt
        t0 = time.time()
        try:
            _playwright_shot(url, path, cfg)
            result.path = path
            result.success = True
            result.duration_ms = (time.time() - t0) * 1000
            return result
        except ImportError:
            result.error = "playwright not installed"
            return result
        except Exception as exc:
            result.error = str(exc)
            result.duration_ms = (time.time() - t0) * 1000
            if attempt <= cfg.retries:
                time.sleep(cfg.retry_delay_s)

    return result


def take_screenshots_batch(
    urls: list[tuple[str, str]],
    cfg: ScreenshotConfig,
) -> list[ScreenshotResult]:
    """
    Batch screenshots. urls = [(url, filename), ...].
    Reużywa jednej instancji przeglądarki dla wszystkich URLi.
    """
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        return _batch_playwright(urls, cfg)
    except ImportError:
        return [
            ScreenshotResult(url=url, error="playwright not installed")
            for url, _ in urls
        ]
    except Exception as exc:
        return [
            ScreenshotResult(url=url, error=str(exc))
            for url, _ in urls
        ]


# ──────────────────────────────────────────────
# Playwright internals
# ──────────────────────────────────────────────

def _playwright_shot(url: str, path: Path, cfg: ScreenshotConfig) -> None:
    """Pojedynczy screenshot przez Playwright (nowa przeglądarka per call)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, wait_until=cfg.wait_until, timeout=cfg.timeout_ms)
            page.screenshot(path=str(path), full_page=cfg.full_page)
        finally:
            browser.close()


def _batch_playwright(
    urls: list[tuple[str, str]],
    cfg: ScreenshotConfig,
) -> list[ScreenshotResult]:
    """Batch screenshots przez jedną instancję przeglądarki."""
    from playwright.sync_api import sync_playwright

    results: list[ScreenshotResult] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            for url, filename in urls:
                path = cfg.output_dir / filename
                result = ScreenshotResult(url=url, attempts=1)
                t0 = time.time()

                for attempt in range(1, cfg.retries + 2):
                    result.attempts = attempt
                    try:
                        page = browser.new_page()
                        try:
                            page.goto(url, wait_until=cfg.wait_until, timeout=cfg.timeout_ms)
                            page.screenshot(path=str(path), full_page=cfg.full_page)
                            result.path = path
                            result.success = True
                            break
                        finally:
                            page.close()
                    except Exception as exc:
                        result.error = str(exc)
                        if attempt <= cfg.retries:
                            time.sleep(cfg.retry_delay_s)

                result.duration_ms = (time.time() - t0) * 1000
                results.append(result)
        finally:
            browser.close()

    return results


# ──────────────────────────────────────────────
# Convenience helper używany z cli.py
# ──────────────────────────────────────────────

def screenshot_endpoint(url: str, slug: str, screenshots_dir: Path) -> Optional[Path]:
    """
    Uproszczony wrapper używany przez cli.py walk.
    Zwraca Path do pliku lub None jeśli nie udało się.
    """
    cfg = ScreenshotConfig(output_dir=screenshots_dir)
    result = take_screenshot(url, f"{slug}.png", cfg)
    return result.path if result.success else None
