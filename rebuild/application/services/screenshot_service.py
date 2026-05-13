from __future__ import annotations
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from ...domain.endpoint import EndpointResult, EndpointStatus
from .base import Service


@dataclass
class ScreenshotConfig:
    output_dir: Path
    timeout_ms: int = 15_000
    retries: int = 2
    retry_delay_s: float = 1.0
    full_page: bool = True
    wait_until: str = "networkidle"


class ScreenshotService(Service[List[EndpointResult], List[EndpointResult]]):
    """
    Service for capturing screenshots of endpoints.
    """

    def __init__(self, config: ScreenshotConfig):
        self.config = config

    def execute(self, endpoint_results: List[EndpointResult]) -> List[EndpointResult]:
        """
        Enriches EndpointResults with screenshot paths.
        """
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Filter GET endpoints that succeeded or failed (not skipped/timeout)
        targets = []
        for er in endpoint_results:
            if er.endpoint.method == "GET" and er.status in (
                EndpointStatus.OK,
                EndpointStatus.FAIL,
            ):
                targets.append(er)

        if not targets:
            return endpoint_results

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            for er in targets:
                er.error = f"{er.error or ''} [screenshot error: playwright not installed]".strip()
            return endpoint_results

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                for er in targets:
                    filename = f"{er.endpoint.slug}.png"
                    path = self.config.output_dir / filename

                    for attempt in range(1, self.config.retries + 2):
                        try:
                            page = browser.new_page()
                            try:
                                page.goto(
                                    er.endpoint.url,
                                    wait_until=self.config.wait_until,
                                    timeout=self.config.timeout_ms,
                                )
                                page.screenshot(path=str(path), full_page=self.config.full_page)
                                er.screenshot_path = path
                                break
                            finally:
                                page.close()
                        except Exception as exc:
                            if attempt > self.config.retries:
                                er.error = f"{er.error or ''} [screenshot error: {exc}]".strip()
                            else:
                                time.sleep(self.config.retry_delay_s)
            finally:
                browser.close()

        return endpoint_results
