from __future__ import annotations

import time
from datetime import date
from pathlib import Path
from typing import List, Optional

from ..domain.models import WalkConfig, DeployMethod
from ..domain.commit import CommitInfo
from ..domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from ..domain.day_result import DayResult
from ..domain.context import EndpointContext

# Tymczasowe importy ze starej struktury (do czasu przeniesienia do infrastructure/services)
from ..git_walker import checkout, days_with_commits, restore_head
from ..deployer import start, stop
from ..endpoint_scanner import scan_endpoints
from ..tester import run_tests
from ..screenshotter import ScreenshotConfig, screenshot_endpoint
from ..reporter import save_day, save_timeline_index

class Pipeline:
    def __init__(self, config: WalkConfig, console=None):
        self.config = config
        self.console = console

    def log(self, message: str):
        if self.console:
            self.console.print(message)

    def run(self) -> List[DayResult]:
        """Główna pętla pipeline'u."""
        commits = days_with_commits(self.config)
        if not commits:
            self.log("[yellow]Brak commitów w podanym przedziale.[/yellow]")
            return []

        self.log(f"Znaleziono [bold]{len(commits)}[/bold] dni z commitami.\n")
        all_results: List[DayResult] = []

        try:
            for day, commit in commits:
                result = self.run_day(day, commit)
                all_results.append(result)
        finally:
            if not self.config.dry_run:
                restore_head(self.config.repo_path)

        # Zbiorczy index
        save_timeline_index(all_results, self.config.output_dir)
        return all_results

    def run_day(self, day: date, commit: CommitInfo) -> DayResult:
        """Przetwarzanie jednego dnia (jednego commita)."""
        day_dir = self.config.output_dir / str(day)
        self.log(f"--- [bold]{day}[/bold]  {commit.sha[:8]}  {commit.message[:60]}")

        t0 = time.time()
        result = DayResult(
            day=day,
            commit=commit,
            deploy_method=self.config.deploy_method,
            deploy_success=False,
            output_dir=day_dir,
        )

        try:
            # 1. Checkout
            if not self.config.dry_run:
                checkout(self.config.repo_path, commit.sha)

            # 2. Deploy
            result.deploy_success = start(self.config.repo_path, self.config)
            if not result.deploy_success and not self.config.dry_run:
                self.log("  [red]✗ deploy failed — skip endpoints[/red]")
                result.duration_seconds = time.time() - t0
                save_day(result)
                return result

            # 3. Skanuj endpointy
            result.endpoints = scan_endpoints(self.config.repo_path, self.config)
            self.log(f"  Endpointów: [bold]{len(result.endpoints)}[/bold]")

            # 4. Testuj endpointy
            # W przyszłości: result.endpoint_results = [self.process_endpoint(EndpointContext(ep, commit, day)) for ep in result.endpoints]
            result.endpoint_results = run_tests(result.endpoints, self.config, day_dir)

            # 4b. Screenshots
            if self.config.screenshots:
                self._attach_screenshots(result, day_dir)

            # 5. Raport
            save_day(result)

        except Exception as exc:
            result.error = str(exc)
            self.log(f"  [red]Błąd: {exc}[/red]")
        finally:
            stop(self.config.repo_path, self.config)
            result.duration_seconds = time.time() - t0

        return result

    def _attach_screenshots(self, result: DayResult, day_dir: Path) -> None:
        """Dodaje screenshoty do istniejących EndpointResult."""
        screenshots_dir = day_dir / "screenshots"
        for ep_result in result.endpoint_results:
            ep = ep_result.endpoint
            if ep.method != "GET" or ep_result.status not in (EndpointStatus.OK, EndpointStatus.FAIL):
                continue
            ep_result.screenshot_path = screenshot_endpoint(ep.url, ep.slug, screenshots_dir)
