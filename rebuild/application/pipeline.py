from __future__ import annotations
import time
import json
from datetime import date
from pathlib import Path
from typing import List, Optional, Set

from ..domain.models import WalkConfig, DeployMethod
from ..domain.commit import CommitInfo
from ..domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from ..domain.day_result import DayResult
from ..domain.context import EndpointContext
from ..domain.events import PipelineEvent

from .services.git_service import GitService
from .services.deploy_service import DeployService
from .services.scanner_service import ScannerService
from .services.test_service import TestService
from .services.screenshot_service import ScreenshotService, ScreenshotConfig
from .services.reporter_service import ReporterService

class Pipeline:
    """
    Orchestrates the analysis process (Command).
    Supports Incremental Walking and Event Sourcing.
    """
    def __init__(self, config: WalkConfig, console=None):
        self.config = config
        self.console = console
        self._event_log: List[PipelineEvent] = []
        
        # Initialize services
        self.git = GitService(config.repo_path)
        self.deploy = DeployService(config)
        self.scanner = ScannerService(config)
        self.tester = TestService(config)
        self.screenshots = ScreenshotService(ScreenshotConfig(output_dir=config.output_dir))
        self.reporter = ReporterService()
        
        # Load incremental state
        self._state_file = config.output_dir / "walk_state.json"
        self._processed_shas: Set[str] = self._load_state()

    def _load_state(self) -> Set[str]:
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
                return set(data.get("processed_shas", []))
            except Exception:
                pass
        return set()

    def _save_state(self):
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        data = {"processed_shas": list(self._processed_shas)}
        self._state_file.write_text(json.dumps(data, indent=2))

    def _emit(self, event_type: str, **kwargs):
        event = PipelineEvent.create(event_type, **kwargs)
        self._event_log.append(event)
        log_file = self.config.output_dir / "history.jsonl"
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(event.to_json() + "\n")

    def log(self, message: str):
        if self.console:
            self.console.print(message)

    def run(self) -> List[DayResult]:
        commits = self.git.days_with_commits(self.config)
        if not commits:
            self.log("[yellow]Brak commitów w podanym przedziale.[/yellow]")
            return []

        self._emit("PIPELINE_STARTED", days=len(commits), repo=str(self.config.repo_path))
        self.log(f"Znaleziono [bold]{len(commits)}[/bold] dni z commitami.\n")
        all_results: List[DayResult] = []

        try:
            for day, commit in commits:
                if commit.sha in self._processed_shas:
                    self.log(f"--- [bold]{day}[/bold]  {commit.sha[:8]}  [dim](skipped — already processed)[/dim]")
                    # In a real scenario, we might want to load previous results to include in all_results
                    continue
                    
                result = self.run_day(day, commit)
                all_results.append(result)
                self._processed_shas.add(commit.sha)
                self._save_state()
        finally:
            if not self.config.dry_run:
                self.git.restore_head()

        self._emit("PIPELINE_FINISHED", total_days=len(all_results))
        self.reporter.save_timeline_index(all_results, self.config.output_dir)
        return all_results

    def run_day(self, day: date, commit: CommitInfo) -> DayResult:
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
                self.git.checkout(commit.sha)
                self._emit("COMMIT_CHECKOUT", sha=commit.sha, day=str(day))

            # 2. Deploy
            self._emit("DEPLOY_STARTED", method=self.config.deploy_method.value)
            result.deploy_success = self.deploy.start(self.config.repo_path)
            self._emit("DEPLOY_FINISHED", success=result.deploy_success)
            
            if not result.deploy_success and not self.config.dry_run:
                self.log("  [red]✗ deploy failed — skip endpoints[/red]")
                result.duration_seconds = time.time() - t0
                self.reporter.save_day(result)
                return result

            # 3. Scan endpoints
            result.endpoints = self.scanner.execute(self.config.repo_path)
            self._emit("SCAN_FINISHED", endpoint_count=len(result.endpoints))
            self.log(f"  Endpointów: [bold]{len(result.endpoints)}[/bold]")

            # 4. Test endpoints
            self.tester.set_day_dir(day_dir)
            result.endpoint_results = self.tester.execute(result.endpoints)
            self._emit("TEST_FINISHED", ok=sum(1 for r in result.endpoint_results if r.status.value == "ok"))

            # 5. Screenshots
            if self.config.screenshots:
                self.screenshots.config.output_dir = day_dir / "screenshots"
                result.endpoint_results = self.screenshots.execute(result.endpoint_results)
                self._emit("SCREENSHOTS_FINISHED")

            # 6. Report
            self.reporter.save_day(result)
            self._emit("DAY_FINISHED", day=str(day), health=result.health_pct)

        except Exception as exc:
            result.error = str(exc)
            self._emit("ERROR_OCCURRED", error=str(exc))
            self.log(f"  [red]Błąd: {exc}[/red]")
        finally:
            self.deploy.stop(self.config.repo_path)
            result.duration_seconds = time.time() - t0

        return result
