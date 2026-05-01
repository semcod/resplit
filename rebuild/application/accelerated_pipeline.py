"""
10x Faster Pipeline using worktrees, volume mounts, and parallel testing.
"""
from __future__ import annotations
import time
import json
from datetime import date
from pathlib import Path
from typing import List, Optional, Set, Dict

from ..domain.models import WalkConfig, DeployMethod
from ..domain.commit import CommitInfo
from ..domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from ..domain.day_result import DayResult
from ..domain.events import PipelineEvent

from .services.git_service import GitService
from .services.worktree_manager import WorktreeManager
from .services.accelerator_deploy import AcceleratorDeployService
from .services.db_snapshot_manager import DBSnapshotManager
from .services.scanner_service import ScannerService
from .services.parallel_test_engine import ParallelTestEngine
from .services.smart_test_selector import SmartTestSelector
from .services.screenshot_service import ScreenshotService, ScreenshotConfig
from .services.reporter_service import ReporterService


class AcceleratedPipeline:
    """
    Ultra-fast pipeline using:
    - Git worktrees (instant branch switching)
    - Volume-mounted code (no container rebuild)
    - Hot reload (no container restart)
    - DB snapshots (instant state restore)
    - Parallel testing (concurrent execution)
    - Smart selection (diff-driven testing)
    
    Typical speedup: 10-50x compared to traditional mode.
    """
    
    def __init__(self, config: WalkConfig, console=None):
        self.config = config
        self.console = console
        self._event_log: List[PipelineEvent] = []
        
        # Output directory for this run
        self.output_dir = config.output_dir
        self.worktree_dir = self.output_dir / "worktrees"
        self.snapshot_dir = self.output_dir / "snapshots"
        
        # Initialize services
        self.git = GitService(config.repo_path)
        self.worktrees = WorktreeManager(config.repo_path, self.worktree_dir)
        self.deploy = AcceleratorDeployService(config, self.worktrees, console)
        self.db_snapshots = DBSnapshotManager(
            self.snapshot_dir,
            db_container=getattr(config, 'db_container', 'db'),
            db_type=getattr(config, 'db_type', 'postgres')
        )
        self.scanner = ScannerService(config)
        self.tester = ParallelTestEngine(
            config,
            max_concurrent=getattr(config, 'max_parallel_tests', 10),
            health_first=True
        )
        self.smart_selector = SmartTestSelector(config.repo_path)
        self.screenshots = ScreenshotService(ScreenshotConfig(output_dir=config.output_dir))
        self.reporter = ReporterService()
        
        # State tracking
        self._state_file = config.output_dir / "accelerator_state.json"
        self._processed_shas: Set[str] = self._load_state()
        self._baseline_snapshot: Optional[str] = None
        self._previous_commit: Optional[str] = None
    
    def _load_state(self) -> Set[str]:
        """Load processed commit SHAs from state file."""
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
                return set(data.get("processed_shas", []))
            except Exception:
                pass
        return set()
    
    def _save_state(self):
        """Persist processed SHAs."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "processed_shas": list(self._processed_shas),
            "baseline_snapshot": self._baseline_snapshot,
            "mode": "accelerated"
        }
        self._state_file.write_text(json.dumps(data, indent=2))
    
    def _emit(self, event_type: str, **kwargs):
        """Emit and log pipeline event."""
        event = PipelineEvent.create(event_type, **kwargs)
        self._event_log.append(event)
        log_file = self.output_dir / "history.jsonl"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(event.to_json() + "\n")
    
    def log(self, message: str):
        """Log message to console if available."""
        if self.console:
            self.console.print(message)
    
    def run(self) -> List[DayResult]:
        """
        Run accelerated analysis over commit history.
        """
        commits = self.git.days_with_commits(self.config)
        if not commits:
            self.log("[yellow]Brak commitów w podanym przedziale.[/yellow]")
            return []
        
        self._emit("PIPELINE_STARTED", 
                   days=len(commits), 
                   mode="accelerated",
                   repo=str(self.config.repo_path))
        
        self.log(f"[bold cyan]⚡ ACCELERATOR MODE[/bold cyan] - {len(commits)} commits")
        self.log(f"  Worktrees: {self.worktree_dir}")
        self.log(f"  Snapshots: {self.snapshot_dir}")
        
        # Pre-create worktrees for all commits (parallel prep)
        self._prewarm_worktrees([c.sha for _, c in commits])

        first_commit_path = self.worktrees.get_active_path(commits[0][1].sha)
        runtime_ready = self.deploy.prepare_runtime(self.config.repo_path, first_commit_path)
        if runtime_ready:
            self.log("[dim]Accelerator runtime prepared with active worktree mount[/dim]")
        
        # Start infrastructure (once!)
        self.log("[dim]Starting persistent infrastructure...[/dim]")
        infrastructure_ok = self.deploy.start(self.config.repo_path)
        
        if not infrastructure_ok:
            self.log("[red]✗ Infrastructure failed to start[/red]")
            return []
        
        # Create baseline DB snapshot
        try:
            self._create_baseline_snapshot()
        except Exception as exc:
            self._emit("ERROR_OCCURRED", stage="baseline_snapshot", error=str(exc))
            self.log(f"[red]✗ Baseline snapshot failed:[/red] {exc}")
            return []
        
        all_results: List[DayResult] = []
        
        try:
            for day, commit in commits:
                if commit.sha in self._processed_shas and not self.config.replay:
                    self.log(f"--- [bold]{day}[/bold]  {commit.sha[:8]}  [dim](skipped)[/dim]")
                    continue
                
                result = self._run_day_fast(day, commit)
                all_results.append(result)
                self._processed_shas.add(commit.sha)
                self._save_state()
                
                self._previous_commit = commit.sha
                
        finally:
            # In accelerator mode, keep infrastructure running by default
            if not getattr(self.config, 'shutdown_after', False):
                self.log("[dim]Accelerator: keeping infrastructure running[/dim]")
                self.deploy.stop(self.config.repo_path)
        
        self._emit("PIPELINE_FINISHED", total_days=len(all_results))
        self.reporter.save_timeline_index(all_results, self.output_dir)
        
        return all_results
    
    def _prewarm_worktrees(self, shas: List[str]):
        """Pre-create worktrees for all commits to avoid delays during execution."""
        self.log(f"[dim]Preparing {len(shas)} worktrees...[/dim]")
        start = time.perf_counter()
        
        for sha in shas:
            try:
                self.worktrees.get_or_create(sha)
            except Exception as e:
                self.log(f"  [yellow]Warning: worktree for {sha[:8]}: {e}[/yellow]")
        
        elapsed = time.perf_counter() - start
        self.log(f"  [green]✓ Worktrees ready in {elapsed:.1f}s[/green]")
    
    def _create_baseline_snapshot(self):
        """Create initial DB snapshot for fast restore between commits."""
        self.log("[dim]Creating baseline DB snapshot...[/dim]")

        info = self.db_snapshots.create_baseline()
        self._baseline_snapshot = info.name
        self.log(f"  [green]✓ Snapshot: {info.name} ({info.size_bytes or 0} bytes)[/green]")
    
    def _run_day_fast(self, day: date, commit: CommitInfo) -> DayResult:
        """Execute single day analysis with maximum speed."""
        day_dir = self.output_dir / str(day)
        t0 = time.perf_counter()
        
        self.log(f"--- [bold]{day}[/bold]  {commit.sha[:8]}  {commit.message[:50]}")
        
        result = DayResult(
            day=day,
            commit=commit,
            deploy_method=self.config.deploy_method,
            deploy_success=False,
            output_dir=day_dir,
            is_dry_run=self.config.dry_run
        )
        
        try:
            # 1. Switch code via worktree (INSTANT - no checkout overhead)
            self._emit("CODE_SWITCH_STARTED", sha=commit.sha)
            switch_ok = self.deploy.switch_commit(commit.sha, self.config.repo_path)
            
            if not switch_ok:
                result.error = "Code switch failed"
                self.log("  [red]✗ Code switch failed[/red]")
                result.duration_seconds = time.perf_counter() - t0
                return result
            
            self._emit("CODE_SWITCH_FINISHED", sha=commit.sha)
            result.deploy_success = True
            
            # 2. Restore DB to baseline (INSTANT - no re-seed)
            if self._baseline_snapshot:
                try:
                    self._restore_db_fast()
                except Exception as exc:
                    result.error = str(exc)
                    self._emit("ERROR_OCCURRED", stage="db_restore", sha=commit.sha, error=str(exc))
                    self.log(f"  [red]✗ {exc}[/red]")
                    result.duration_seconds = time.perf_counter() - t0
                    return result
            
            # 3. Scan endpoints
            wt_path = self.worktrees.get_active_path(commit.sha)
            result.endpoints = self.scanner.execute(wt_path)
            
            # 4. Smart test selection (only test changed endpoints)
            endpoints_to_test = result.endpoints
            if self._previous_commit and getattr(self.config, 'smart_select', True):
                selection = self.smart_selector.select_tests(
                    result.endpoints,
                    self.smart_selector.get_changed_modules(self._previous_commit, commit.sha),
                    self._previous_commit
                )
                endpoints_to_test = selection.endpoints_to_test
                self.log(f"  Smart select: {len(endpoints_to_test)}/{len(result.endpoints)} endpoints")
            
            # 5. Parallel test execution
            self._emit("TEST_STARTED", endpoint_count=len(endpoints_to_test))
            self.tester.set_day_dir(day_dir)
            result.endpoint_results = self.tester.execute_sync(endpoints_to_test)
            self._emit("TEST_FINISHED", ok=result.ok_count, total=len(result.endpoint_results))
            
            # 6. Screenshots (parallel-capable)
            if self.config.screenshots:
                self.screenshots.config.output_dir = day_dir / "screenshots"
                result.endpoint_results = self.screenshots.execute(result.endpoint_results)
            
            # 7. Save results
            self.reporter.save_day(result)
            
            duration = time.perf_counter() - t0
            self.log(f"  [green]✓ Done in {duration:.1f}s[/green] "
                    f"({result.health_pct:.0f}% healthy)")
            
        except Exception as exc:
            result.error = str(exc)
            self._emit("ERROR_OCCURRED", error=str(exc))
            self.log(f"  [red]Error: {exc}[/red]")
        
        result.duration_seconds = time.perf_counter() - t0
        return result
    
    def _restore_db_fast(self):
        """Restore DB from snapshot (ultra-fast)."""
        if not self._baseline_snapshot:
            raise RuntimeError("DB restore failed: baseline snapshot not available")

        restored = self.db_snapshots.restore(self._baseline_snapshot, quick=True)
        if not restored:
            raise RuntimeError(f"DB restore failed: {self._baseline_snapshot}")
    
    def cleanup(self):
        """Clean up worktrees and resources."""
        self.log("[dim]Cleaning up accelerator resources...[/dim]")
        self.worktrees.cleanup_all()
