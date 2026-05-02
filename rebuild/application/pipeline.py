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

from .base_pipeline import BasePipeline
from .services.deploy_service import DeployService
from .services.test_service import TestService

class Pipeline(BasePipeline):
    """
    Orchestrates the analysis process (Command).
    Supports Incremental Walking, Event Sourcing, and Replay Mode.
    """
    def __init__(self, config: WalkConfig, console=None):
        super().__init__(config, console)
        self.deploy = DeployService(config, console=self.console)
        self.tester = TestService(config)

    def _check_for_manual_fix(self, walk_git: GitService, original_sha: str) -> Optional[str]:
        """
        Check for manual recovery commits in the clone that target the original commit.
        Expected commit subject marker: rebuild-fix:<sha>
        """
        markers = (
            f"rebuild-fix:{original_sha}".lower(),
            f"rebuild-fix:{original_sha[:8]}".lower(),
        )
        commands = [
            ["git", "log", "--all", "--format=%H%x09%s"],
            ["git", "reflog", "--all", "--format=%H%x09%gs"],
        ]
        seen: Set[str] = set()

        for cmd in commands:
            try:
                result = walk_git.shell.run(cmd, cwd=walk_git.repo_path)
                if result.returncode != 0:
                    continue

                for line in result.stdout.splitlines():
                    if "\t" not in line:
                        continue
                    sha, message = line.split("\t", 1)
                    if not sha or sha in seen:
                        continue
                    seen.add(sha)

                    normalized = message.lower()
                    if "rebuild-fix:" not in normalized:
                        continue
                    if any(marker in normalized for marker in markers):
                        return sha
            except Exception:
                continue

        return None

    def run(self) -> List[DayResult]:
        commits = self.git.days_with_commits(self.config)
        if not commits:
            self.log("[yellow]Brak commitów w podanym przedziale.[/yellow]")
            return []

        self._event_service.enable()
        self._emit("PIPELINE_STARTED", days=len(commits), repo=str(self.config.repo_path), replay=self.config.replay)
        self.log(f"Znaleziono [bold]{len(commits)}[/bold] dni z commitami.\n")
        
        # Clone repo into output_dir/repo/ so original is never modified
        if not self.config.dry_run:
            if self.config.accelerator:
                self.log("[bold cyan]⚡ Accelerator Mode: Synchronizowanie stanu aktualnego (node_modules)...[/bold cyan]")
                clone_path = self.config.output_dir / "repo"
                self.git.sync_current_state(clone_path)
                self._walk_git = GitService(clone_path)
            else:
                self.log("[dim]Klonowanie repo do .rebuild/repo/ ...[/dim]")
                self._walk_git = self.git.clone_for_walk(self.config.output_dir)
        else:
            self._walk_git = self.git

        if self.config.replay:
            self.log("[bold magenta]⚡ Replay Mode: Utrzymywanie stałej infrastruktury.[/bold magenta]")
            self.deploy.start(self._walk_git.repo_path)

        all_results: List[DayResult] = []

        try:
            for day, commit in commits:
                if commit.sha in self._processed_shas:
                    self.log(f"--- [bold]{day}[/bold]  {commit.sha[:8]}  [dim](skipped — already processed)[/dim]")
                    continue

                result = self.run_day(day, commit)
                all_results.append(result)

                failed = bool(result.error) or (not result.deploy_success and not self.config.dry_run)
                if failed:
                    self.log(
                        f"  [yellow]Recovery pending for {commit.sha[:8]}[/yellow] "
                        f"(commit fix in clone with message 'rebuild-fix:{commit.sha[:8]}' and rerun)"
                    )
                    continue

                self._processed_shas.add(commit.sha)
                self._save_state()
        finally:
            walk_git = getattr(self, "_walk_git", self.git)
            self.deploy.stop(walk_git.repo_path)
            self._event_service.disable()

        self._emit("PIPELINE_FINISHED", total_days=len(all_results))
        self.reporter.save_timeline_index(all_results, self.config.output_dir)
        return all_results

    def run_day(self, day: date, commit: CommitInfo) -> DayResult:
        day_dir = self.config.output_dir / str(day)
        self.log(f"--- [bold]{day}[/bold]  {commit.sha[:8]}  {commit.message[:60]}")

        t0 = time.perf_counter()
        result = DayResult(
            day=day,
            commit=commit,
            deploy_method=self.config.deploy_method,
            deploy_success=False,
            output_dir=day_dir,
            is_dry_run=self.config.dry_run
        )

        walk_git = getattr(self, "_walk_git", self.git)
        manual_patch_dir = self.config.output_dir / "patch"

        try:
            # 1. Checkout in clone (original repo untouched)
            if not self.config.dry_run:
                walk_git.checkout(commit.sha)
                self._emit("COMMIT_CHECKOUT", sha=commit.sha, day=str(day))

                overrides = self.patcher.apply_manual_overrides(manual_patch_dir, walk_git.repo_path)
                if overrides:
                    self.log(f"  [dim]Manual override: applied {overrides} file(s) from {manual_patch_dir}[/dim]")
                    self._emit("MANUAL_OVERRIDE_APPLIED", files=overrides, source=str(manual_patch_dir))

                # Check for manual fix commit in clone (for health recovery)
                fix_sha = self._check_for_manual_fix(walk_git, commit.sha)
                if fix_sha:
                    self.log(f"  [cyan]Manual fix detected: {fix_sha[:8]}, applying...[/cyan]")
                    walk_git.checkout(fix_sha)
                    self._emit("MANUAL_FIX_APPLIED", original_sha=commit.sha, fix_sha=fix_sha)

            # Clone path for static file scanning; original path for docker
            scan_repo = walk_git.repo_path

            if self.config.accelerator and not self.config.dry_run:
                patched = self.patcher.execute(scan_repo)
                if patched:
                    self.log(f"  [dim]Spatchowano {patched} plików Dockerfile (accelerator).[/dim]")

            # 3. Apply manual overrides (fixes for historical bugs)
            if self.config.patch_dir and not self.config.dry_run:
                overridden = self.overrider.execute(scan_repo, self.config.patch_dir)
                if overridden:
                    self.log(f"  [bold green]✓ Zastosowano {overridden} poprawek manualnych.[/bold green]")

            # 2. Deploy/Reload
            self.deploy.day_dir = day_dir
            if self.config.replay:
                self._emit("DEPLOY_RELOAD_STARTED", service=self.config.app_service)
                result.deploy_success = self.deploy.reload(walk_git.repo_path)
                result.deploy_log = self.deploy.last_log
                result.deploy_error_category = self.deploy.last_error_category
                self._emit("DEPLOY_RELOAD_FINISHED", success=result.deploy_success)
            else:
                result.deploy_success = self.deploy.start(walk_git.repo_path)
                result.deploy_log = self.deploy.last_log
                result.deploy_error_category = self.deploy.last_error_category
                self._emit("DEPLOY_FINISHED", success=result.deploy_success)

            if not result.deploy_success and not self.config.dry_run:
                self.log("  [red]✗ deploy/reload failed — skip endpoints[/red]")
                result.duration_seconds = time.perf_counter() - t0
                self.reporter.save_day(result)
                return result

            # 3. Scan endpoints (uses clone for static openapi.json lookup)
            result.endpoints = self.scanner.execute(scan_repo)
            self._emit("SCAN_FINISHED", endpoint_count=len(result.endpoints))
            self.log(f"  Endpointów: [bold]{len(result.endpoints)}[/bold]")

            # 4. Test endpoints
            self.tester.set_day_dir(day_dir)
            result.endpoint_results = self.tester.execute(result.endpoints)
            self._emit("TEST_FINISHED", ok=result.ok_count)

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
            if not self.config.replay:
                self.deploy.stop(walk_git.repo_path)
            result.duration_seconds = time.perf_counter() - t0

        return result
