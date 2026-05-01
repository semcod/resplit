from __future__ import annotations
import time
import hashlib
import json
from pathlib import Path
from typing import Optional, List, Any

from rich.console import Console

from ...domain.models import DeployMethod, WalkConfig
from ...domain.day_result import DeployErrorCategory
from .base import Service
from ...infrastructure.shell_adapter import ShellAdapter
from ...infrastructure.http_adapter import HttpAdapter

class DeployService(Service[Path, bool]):
    """
    Service for managing the lifecycle of the service being analyzed.
    Supports 'Replay Mode' (Invariant Infrastructure).
    """
    def __init__(self, config: WalkConfig, console: Optional[Console] = None, shell: Optional[ShellAdapter] = None, http: Optional[HttpAdapter] = None):
        self.config = config
        self.console = console or Console()
        self.shell = shell or ShellAdapter(self.console)
        self.http = http or HttpAdapter(timeout=5)
        self._uvicorn_proc: Optional[Any] = None
        self._project_name = f"rebuild-{hashlib.md5(str(config.repo_path.resolve()).encode()).hexdigest()[:8]}"
        self.last_log: Optional[str] = None
        self.last_error_category: Optional[DeployErrorCategory] = None
        self.day_dir: Optional[Path] = None

    def detect_deploy_method(self, repo: Path) -> DeployMethod:
        for name in (self.config.compose_file, "docker-compose.yml", "docker-compose.yaml"):
            if (repo / name).exists():
                return DeployMethod.DOCKER_COMPOSE
        for candidate in ("server.py", Path("backend") / "server.py"):
            if (repo / candidate).exists():
                return DeployMethod.UVICORN
        return DeployMethod.NONE

    def start(self, repo: Path) -> bool:
        method = self.config.deploy_method
        if method == DeployMethod.NONE or self.config.dry_run:
            return True

        # In replay mode: infra is already up — just verify health
        if self.config.replay:
            self.console.print(f"  [dim]replay: checking existing infra health...[/dim]")
            return self._wait_healthy_with_retry()

        if method == DeployMethod.DOCKER_COMPOSE:
            return self._run_with_retry(lambda: self._compose_up(repo), action_label="deploy")
        if method == DeployMethod.UVICORN:
            return self._run_with_retry(lambda: self._uvicorn_start(repo), action_label="deploy")
        return False

    def execute(self, repo: Path) -> bool:
        """Implements Service protocol."""
        return self.start(repo)

    def wait_healthy(self, timeout: Optional[float] = None, interval: Optional[float] = None) -> bool:
        """Public health gate for callers that need to re-check app readiness."""
        return self._wait_healthy(timeout=timeout, interval=interval)

    def reload(self, repo: Path) -> bool:
        """
        Performs a fast reload of the application in Replay Mode.
        Restarts only the specified app service container by name.
        Does NOT use compose project name — works with externally started infra.
        In replay mode, syncs checked-out code into runtime before restart.
        """
        service = self.config.app_service or "backend"

        if self.config.deploy_method == DeployMethod.DOCKER_COMPOSE:
            # Ensure runtime gets code from current checkout (replay correctness)
            if not self._sync_code_to_runtime(repo, service):
                self.last_log = "Replay sync failed: runtime code not updated"
                self.console.print(
                    "  [red]Replay sync failed:[/red] checkout was not copied to runtime; aborting reload"
                )
                return False

            # Try restarting by container name directly (works regardless of compose project)
            self.console.print(f"  [bold cyan]docker restart {service}[/bold cyan]")
            result = self.shell.run(["docker", "restart", service])
            if result.returncode != 0:
                # Fallback: compose restart with explicit file
                self.console.print(f"  [dim]Fallback: compose restart...[/dim]")
                try:
                    cf = self._compose_file(repo)
                    result = self.shell.run(
                        ["docker", "compose", "-f", str(cf), "restart", service],
                        cwd=repo
                    )
                except FileNotFoundError:
                    pass
            if result.returncode != 0:
                self.last_log = result.stderr
                self.console.print(f"  [red]Restart failed:[/red] {result.stderr[:200]}")
                return False
        else:
            return self.start(repo)

        return self._wait_healthy_with_retry()

    def stop(self, repo: Path) -> None:
        if self.config.dry_run or self.config.deploy_method == DeployMethod.NONE:
            return
        # In replay mode: leave infrastructure running — don't tear down
        if self.config.replay:
            self.console.print("  [dim]replay: leaving infra running[/dim]")
            return
        if self.config.deploy_method == DeployMethod.DOCKER_COMPOSE:
            self._compose_down(repo)
        elif self.config.deploy_method == DeployMethod.UVICORN:
            self._uvicorn_stop()

    def _compose_file(self, repo: Path) -> Path:
        explicit = repo / self.config.compose_file
        if explicit.exists(): return explicit
        for name in ("docker-compose.yml", "docker-compose.yaml"):
            p = repo / name
            if p.exists(): return p
        raise FileNotFoundError(f"Nie znaleziono pliku docker-compose w {repo}")

    def _compose_up(self, repo: Path) -> bool:
        cf = self._compose_file(repo)
        cmd = ["docker", "compose", "-p", self._project_name, "-f", str(cf), "up", "-d", "--build", "--force-recreate"]
        self.console.print(f"  [bold cyan]docker compose up[/bold cyan] (project: {self._project_name})")
        result = self.shell.run(cmd, cwd=repo)
        combined = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0:
            self.last_log = combined
            self.last_error_category = self._classify_deploy_error(combined)
            self.console.print(f"  [red]docker compose up failed:[/red]\n{combined[:500]}")
            self._save_deploy_debug(repo, combined)
            return False
        ok = self.wait_healthy()
        if not ok:
            self.last_error_category = DeployErrorCategory.HEALTH_TIMEOUT
        return ok

    def _compose_down(self, repo: Path) -> None:
        try:
            cf = self._compose_file(repo)
            cmd = ["docker", "compose", "-p", self._project_name, "-f", str(cf), "down", "--remove-orphans", "-v"]
            self.shell.run(cmd, cwd=repo)
        except Exception as e:
            self.console.print(f"  [yellow]docker compose down error: {e}[/yellow]")

    def _uvicorn_start(self, repo: Path) -> bool:
        module = "backend.server:app" if (repo / "backend" / "server.py").exists() else "server:app"
        cmd = ["uvicorn", module, "--host", "0.0.0.0", "--port", "8003", "--reload"]
        self.console.print(f"  [bold cyan]uvicorn[/bold cyan] {module}")
        self._uvicorn_proc = self.shell.popen(cmd, cwd=repo)
        return self.wait_healthy()

    def _uvicorn_stop(self) -> None:
        if self._uvicorn_proc:
            self._uvicorn_proc.terminate()
            self._uvicorn_proc = None

    def _classify_deploy_error(self, log: str) -> DeployErrorCategory:
        log_lower = log.lower()
        if any(p in log_lower for p in ("bind: address already in use", "port is already allocated", "address already in use")):
            return DeployErrorCategory.PORT_CONFLICT
        if any(p in log_lower for p in ("build failed", "dockerfile", "error building", "step ", "failed to build")):
            return DeployErrorCategory.COMPOSE_BUILD_FAIL
        if any(p in log_lower for p in ("migration", "alembic", "flyway", "migrate")):
            return DeployErrorCategory.MIGRATION_FAIL
        if any(p in log_lower for p in ("missing required env", "environment variable", "no such variable", "env not set", "keyerror")):
            return DeployErrorCategory.MISSING_ENV
        return DeployErrorCategory.UNKNOWN

    def _save_deploy_debug(self, repo: Path, log: str) -> None:
        try:
            debug_file = self.config.output_dir / "deploy_debug.txt"
            debug_file.parent.mkdir(parents=True, exist_ok=True)
            with open(debug_file, "a", encoding="utf-8") as f:
                import datetime
                f.write(f"\n=== {datetime.datetime.now().isoformat()} repo={repo} ===\n")
                f.write(log[:5000])
                f.write("\n")
        except Exception:
            pass

    def _run_with_retry(self, action, action_label: str) -> bool:
        attempts = max(1, int(getattr(self.config, "deploy_retry_attempts", 3)))
        backoff = float(getattr(self.config, "deploy_retry_backoff_seconds", 5.0))  
        multiplier = float(getattr(self.config, "deploy_retry_backoff_multiplier", 3.0))

        for attempt in range(1, attempts + 1):
            ok = action()
            if ok:
                if attempt > 1:
                    self.console.print(f"  [green]✓ {action_label} recovered on retry {attempt}/{attempts}[/green]")
                return True

            if attempt < attempts:
                sleep_seconds = max(0.0, backoff * (multiplier ** (attempt - 1)))
                self.console.print(
                    f"  [yellow]{action_label} failed[/yellow] (attempt {attempt}/{attempts}), retry in {sleep_seconds:.1f}s"
                )
                time.sleep(sleep_seconds)

        return False

    def _wait_healthy_with_retry(self) -> bool:
        attempts = max(1, int(getattr(self.config, "deploy_retry_attempts", 3)))
        backoff = float(getattr(self.config, "deploy_retry_backoff_seconds", 5.0))
        multiplier = float(getattr(self.config, "deploy_retry_backoff_multiplier", 3.0))

        for attempt in range(1, attempts + 1):
            if self.wait_healthy():
                if attempt > 1:
                    self.console.print(f"  [green]✓ health recovered on retry {attempt}/{attempts}[/green]")
                return True

            if attempt < attempts:
                sleep_seconds = max(0.0, backoff * (multiplier ** (attempt - 1)))
                self.console.print(
                    f"  [yellow]health check failed[/yellow] (attempt {attempt}/{attempts}), retry in {sleep_seconds:.1f}s"
                )
                time.sleep(sleep_seconds)

        return False

    def _wait_healthy(self, timeout: Optional[float] = None, interval: Optional[float] = None) -> bool:
        health_timeout = self.config.health_timeout if timeout is None else timeout
        health_interval = self.config.health_interval if interval is None else interval
        deadline = time.time() + health_timeout
        last_status: Optional[int] = None
        last_body: Optional[str] = None
        last_error: Optional[str] = None
        while time.time() < deadline:
            try:
                r = self.http.get(self.config.health_url)
                last_status = r.status_code
                last_body = r.text[:500]
                if r.status_code < 500:
                    self.console.print(f"  [green]✓ healthy[/green] ({self.config.health_url})")
                    return True
            except Exception as exc:
                last_error = str(exc)
            time.sleep(health_interval)

        if getattr(self.config, "health_verbose", False):
            if last_status is not None:
                self.console.print(
                    f"  [dim]health last response:[/dim] status={last_status}, body={last_body or '<empty>'}"
                )
            if last_error:
                self.console.print(f"  [dim]health last error:[/dim] {last_error}")

        if getattr(self.config, "health_verbose", False) and self.day_dir:
            try:
                debug_file = self.day_dir / "deploy_debug.txt"
                debug_file.parent.mkdir(parents=True, exist_ok=True)
                with open(debug_file, "a", encoding="utf-8") as f:
                    import datetime
                    f.write(f"\n=== health timeout {datetime.datetime.now().isoformat()} url={self.config.health_url} ===\n")
                    if last_status is not None:
                        f.write(f"status={last_status} body={last_body or '<empty>'}\n")
                    if last_error:
                        f.write(f"error={last_error}\n")
            except Exception:
                pass

        self.console.print(f"  [red]✗ health timeout ({health_timeout}s)[/red]")
        self.last_error_category = DeployErrorCategory.HEALTH_TIMEOUT
        return False

    def _sync_code_to_runtime(self, repo: Path, service: str) -> bool:
        """Copy checked-out repository into /app of the running service container."""
        container = self._resolve_container_name(repo, service)
        if not container:
            return False

        # Detect read-only mounts that block direct code sync.
        # Use code overlay strategy: copy to /tmp/rebuild-overlay and adjust PYTHONPATH.
        mounts = self.shell.run(["docker", "inspect", "-f", "{{json .Mounts}}", container])
        if mounts.returncode == 0:
            try:
                data = json.loads(mounts.stdout.strip() or "[]")
                ro_app_mounts = [
                    m.get("Destination", "")
                    for m in data
                    if not m.get("RW", True) and str(m.get("Destination", "")).startswith("/app")
                ]
                if ro_app_mounts:
                    self.console.print(
                        f"  [dim]Using code overlay for read-only mounts:[/dim] {', '.join(ro_app_mounts[:3])}"
                    )
                    return self._sync_via_overlay(repo, container)
            except Exception:
                pass

        prep = self.shell.run(["docker", "exec", container, "mkdir", "-p", "/app"])
        if prep.returncode != 0:
            return False

        copy = self.shell.run(["docker", "cp", f"{repo}/.", f"{container}:/app/"])
        return copy.returncode == 0

    def _sync_via_overlay(self, repo: Path, container: str) -> bool:
        """Copy checkout to /tmp/rebuild-overlay and set PYTHONPATH to use it."""
        overlay_dir = "/tmp/rebuild-overlay"

        # Clean and create overlay directory
        clean = self.shell.run(["docker", "exec", container, "rm", "-rf", overlay_dir])
        prep = self.shell.run(["docker", "exec", container, "mkdir", "-p", overlay_dir])
        if prep.returncode != 0:
            return False

        # Copy checkout to overlay
        copy = self.shell.run(["docker", "cp", f"{repo}/.", f"{container}:{overlay_dir}/"])
        if copy.returncode != 0:
            return False

        # Persist PYTHONPATH via docker update so it survives restart
        update = self.shell.run(
            ["docker", "update", "-e", f"PYTHONPATH={overlay_dir}:$PYTHONPATH", container]
        )
        if update.returncode != 0:
            self.console.print(f"  [yellow]Failed to update PYTHONPATH:[/yellow] {update.stderr[:200]}")
            return False

        return True

    def _resolve_container_name(self, repo: Path, service: str) -> Optional[str]:
        """Resolve runtime container name from direct name or compose service."""
        direct = self.shell.run(["docker", "inspect", service])
        if direct.returncode == 0:
            return service

        try:
            cf = self._compose_file(repo)
        except FileNotFoundError:
            return None

        lookup = self.shell.run(
            ["docker", "compose", "-f", str(cf), "ps", "-q", service],
            cwd=repo,
        )
        cid = lookup.stdout.strip() if lookup.returncode == 0 else ""
        if cid:
            return cid

        # Fallback for replay mode when compose project name differs from runtime
        # (e.g., cloned repo path or custom project naming).
        by_label = self.shell.run(
            [
                "docker",
                "ps",
                "--filter",
                f"label=com.docker.compose.service={service}",
                "--format",
                "{{.Names}}",
            ]
        )
        names = [line.strip() for line in by_label.stdout.splitlines() if line.strip()]
        return names[0] if names else None
