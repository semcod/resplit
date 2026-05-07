"""
Accelerated deployment using volume mounts + worktrees.
No container recreation - code is swapped via bind mount.
"""
from __future__ import annotations
import time
from pathlib import Path
from typing import Optional, Dict

from .deploy_service import DeployService
from .worktree_manager import WorktreeManager
from ...domain.models import DeployMethod, WalkConfig
from ...infrastructure.shell_adapter import ShellAdapter
from ...infrastructure.http_adapter import HttpAdapter


class AcceleratorDeployService(DeployService):
    """
    10x faster deployment using:
    1. Git worktrees (instant code checkout)
    2. Bind volume mounts (no container rebuild)
    3. Hot reload / signal-based restart (no container restart)

    Instead of:
        docker compose up --build --force-recreate

    We do:
        1. git worktree add ../wt_COMMIT_SHA COMMIT_SHA
        2. Bind mount wt_COMMIT_SHA → /app in running container
        3. Send SIGHUP or touch reload file
        4. Container reloads code instantly
    """

    def __init__(
        self,
        config: WalkConfig,
        worktree_manager: WorktreeManager,
        console=None,
        shell: Optional[ShellAdapter] = None,
        http: Optional[HttpAdapter] = None
    ):
        super().__init__(config, console, shell, http)
        self.worktrees = worktree_manager
        self._current_sha: Optional[str] = None
        self._initial_setup_done = False
        self._volume_name = f"rebuild-code-{self._project_name}"
        self._live_bind_swap_enabled = False
        self._runtime_compose_file: Optional[Path] = None
        self._runtime_marker_filename = ".rebuild_runtime_sha"
        self._last_health_success_at: Optional[float] = None
        self._container_name_cache: Dict[str, str] = {}
        self._reload_strategy_cache: Dict[str, str] = {}

    def start(self, repo: Path) -> bool:
        """
        Initial infrastructure startup.
        Creates long-running containers that will have code swapped via volumes.
        """
        if self.config.dry_run or self.config.deploy_method == DeployMethod.NONE:
            return True

        if self._initial_setup_done:
            return self._wait_healthy()

        if self.config.deploy_method == DeployMethod.DOCKER_COMPOSE:
            return self._accelerated_compose_up(repo)

        # Fallback to parent for UVICORN
        return super().start(repo)

    def prepare_runtime(self, repo: Path, code_path: Path) -> bool:
        """
        Prepare a long-running runtime that mounts a stable "active" path.
        """
        if self.config.deploy_method != DeployMethod.DOCKER_COMPOSE:
            return False

        compose_file = self._compose_file(repo)
        self._set_active_path(code_path)
        runtime_compose = self.setup_mount_compose(repo, compose_file)

        if runtime_compose == compose_file:
            self._runtime_compose_file = None
            self._live_bind_swap_enabled = False
            return False

        self._runtime_compose_file = runtime_compose
        self._live_bind_swap_enabled = True
        return True

    def _accelerated_compose_up(self, repo: Path) -> bool:
        """
        Start containers WITHOUT building or recreating.
        Use pre-built images, mount code as volume.
        """
        cf = self._runtime_compose_file or self._compose_file(repo)

        # Start infrastructure first (DB, cache - these don't change)
        self.console.print("  [bold cyan]Starting persistent infrastructure...[/bold cyan]")

        # Use -d but NOT --build --force-recreate
        # Containers will start with placeholder or empty /app
        cmd = [
            "docker", "compose", "-p", self._project_name, "-f", str(cf),
            "up", "-d", "--no-build"
        ]

        result = self.shell.run(cmd, cwd=repo)
        if result.returncode != 0:
            self.console.print(f"  [red]Compose up failed:[/red] {result.stderr[:300]}")
            return False

        self._initial_setup_done = True
        return self.wait_healthy()

    def switch_commit(self, sha: str, repo: Path) -> bool:
        """
        Switch to different commit WITHOUT restarting container.

        1. Get/create worktree for commit
        2. Update bind mount to point to new worktree
        3. Trigger hot reload
        """
        if self.config.deploy_method != DeployMethod.DOCKER_COMPOSE:
            # Fallback: use parent reload
            return self.reload(repo)

        if self._current_sha == sha:
            return True  # Already on this commit

        self.console.print(f"  [dim]Switching to {sha[:8]}...[/dim]")

        # 1. Ensure worktree exists
        wt_info = self.worktrees.get_or_create(sha)
        self._write_runtime_marker(wt_info.path, sha)

        # 2. Update container bind mount
        service = self.config.app_service or "backend"

        success = False
        if self._live_bind_swap_enabled:
            success = self._update_bind_mount(service, wt_info.path)

        if not success:
            # Fallback/default: copy code into the running container.
            # This keeps infra alive and avoids false-positive "switches"
            # when no live bind-swap runtime is actually configured.
            success = self._sync_code_to_container(service, wt_info.path, sha=sha, repo=repo)

        if not success:
            self.console.print("  [yellow]Switch failed, falling back to restart...[/yellow]")
            # Fallback: traditional restart
            return self.reload(repo)

        # 3. Trigger hot reload
        self._current_sha = sha
        self._trigger_reload(service)

        # 4. Wait for a short health confirmation after code swap.
        if not self._wait_post_switch_healthy():
            return False

        # 5. Verify runtime really points to requested commit
        if not self._verify_runtime_commit(service, sha):
            self.console.print(
                f"  [red]Runtime verification failed:[/red] expected {sha[:8]} in /app/{self._runtime_marker_filename}"
            )
            return False

        return True

    def _update_bind_mount(self, service: str, code_path: Path) -> bool:
        """
        Update bind mount to point to new code path.

        This uses docker's ability to update mounts on running containers
        via volume plugins or by using a shared mount point.

        Strategy: Use a symlink approach:
        - Mount /rebuild-active-code → container:/app
        - Update symlink /rebuild-active-code → actual worktree
        """
        try:
            self._set_active_path(code_path)

            # Touch reload trigger file if app supports it
            trigger_file = code_path / ".reload"
            trigger_file.touch()

            return True
        except Exception as e:
            self.console.print(f"  [dim]Symlink update: {e}[/dim]")
            return False

    _INCREMENTAL_FILE_THRESHOLD = 20

    def _sync_code_to_container(
        self,
        service: str,
        code_path: Path,
        sha: Optional[str] = None,
        repo: Optional[Path] = None,
    ) -> bool:
        """
        Copy code into running container.
        Uses incremental per-file copy when git diff is small (<= threshold),
        falls back to full docker cp otherwise.
        """
        container_name = self._get_container_name(service)

        # Incremental path: git diff to find exactly what changed
        if sha and repo and self._current_sha and self._current_sha != sha:
            changed = self._get_changed_files(repo, self._current_sha, sha)
            if changed is not None and len(changed) <= self._INCREMENTAL_FILE_THRESHOLD:
                self.console.print(
                    f"  [dim]incremental sync: {len(changed)} file(s)[/dim]"
                )
                return self._copy_changed_files(container_name, code_path, changed)

        # Full copy fallback
        self.shell.run(["docker", "exec", container_name, "mkdir", "-p", "/app"])
        result = self.shell.run(
            ["docker", "cp", str(code_path) + "/.", f"{container_name}:/app/"]
        )
        return result.returncode == 0

    def _get_changed_files(
        self, repo: Path, from_sha: str, to_sha: str
    ) -> Optional[list]:
        """Return list of files changed between two commits, or None on error."""
        result = self.shell.run(
            ["git", "diff", "--name-only", from_sha, to_sha],
            cwd=repo,
        )
        if result.returncode != 0:
            return None
        return [f for f in result.stdout.strip().splitlines() if f]

    def _copy_changed_files(
        self, container_name: str, code_path: Path, files: list
    ) -> bool:
        """Copy only the listed relative paths into /app in the container."""
        for rel_path in files:
            src = code_path / rel_path
            if not src.exists():
                # Deleted in this commit - remove from container
                self.shell.run(
                    ["docker", "exec", container_name, "rm", "-f", f"/app/{rel_path}"]
                )
            else:
                parent = Path(rel_path).parent
                if str(parent) != ".":
                    self.shell.run(
                        ["docker", "exec", container_name, "mkdir", "-p", f"/app/{parent}"]
                    )
                result = self.shell.run(
                    ["docker", "cp", str(src), f"{container_name}:/app/{rel_path}"]
                )
                if result.returncode != 0:
                    return False
        return True

    def _get_container_name(self, service: str) -> str:
        """Get full container name for service."""
        cached_name = self._container_name_cache.get(service)
        if cached_name:
            return cached_name

        # Try common naming patterns
        candidates = [
            service,
            f"{self._project_name}-{service}-1",
            f"{self._project_name}_{service}_1",
        ]

        for name in candidates:
            result = self.shell.run(["docker", "inspect", "-f", "{{.State.Status}}", name])
            if result.returncode == 0:
                self._container_name_cache[service] = name
                return name

        # Fallback: try to get from compose
        result = self.shell.run([
            "docker", "compose", "-p", self._project_name,
            "ps", "-q", service
        ])
        if result.returncode == 0 and result.stdout.strip():
            container_name = result.stdout.strip()[:12]
            self._container_name_cache[service] = container_name
            return container_name

        return service  # Last resort

    def _trigger_reload(self, service: str):
        """
        Trigger application reload without container restart.
        Methods in order of preference:
        1. SIGHUP signal (if app handles it)
        2. Touch reload file (for file-watchers like uvicorn --reload)
        3. HTTP reload endpoint (if app exposes one)
        4. Process restart inside container (kill -HUP PID)
        """
        container_name = self._get_container_name(service)

        # Method 1: Touch reload file (works with uvicorn --reload, nodemon, etc)
        wt_path = self.worktrees.get_active_path(self._current_sha) if self._current_sha else None
        if wt_path:
            trigger = wt_path / ".reload"
            trigger.write_text(str(time.time()))

        strategy = self._reload_strategy_cache.get(service)
        if strategy == "signal":
            self._send_hup_signal(container_name)
        elif strategy == "exec":
            self._send_exec_hup(container_name)
        else:
            signal_result = self._send_hup_signal(container_name)
            if signal_result.returncode == 0:
                self._reload_strategy_cache[service] = "signal"
            else:
                exec_result = self._send_exec_hup(container_name)
                if exec_result.returncode == 0:
                    self._reload_strategy_cache[service] = "exec"

        # Small delay to let reload start
        time.sleep(0.5)

    def _send_hup_signal(self, container_name: str):
        return self.shell.run([
            "docker", "kill", "--signal=HUP", container_name
        ])

    def _send_exec_hup(self, container_name: str):
        return self.shell.run([
            "docker", "exec", container_name,
            "sh", "-c", "kill -HUP $(pgrep -f 'uvicorn|python' | head -1) 2>/dev/null || true"
        ])

    def _write_runtime_marker(self, code_path: Path, sha: str) -> None:
        code_path.mkdir(parents=True, exist_ok=True)
        marker = code_path / self._runtime_marker_filename
        marker.write_text(sha, encoding="utf-8")

    def _post_switch_health_timeout(self) -> float:
        return min(5.0, float(self.config.health_timeout))

    def _post_switch_health_interval(self) -> float:
        return min(1.0, float(self.config.health_interval))

    def _post_switch_health_cache_ttl(self) -> float:
        return min(2.0, self._post_switch_health_timeout())

    def _wait_post_switch_healthy(self) -> bool:
        now = time.monotonic()
        if self._last_health_success_at is not None:
            age = now - self._last_health_success_at
            if age <= self._post_switch_health_cache_ttl():
                self.console.print(f"  [dim]health cache hit[/dim] ({age:.2f}s old)")
                return True

        healthy = self.wait_healthy(
            timeout=self._post_switch_health_timeout(),
            interval=self._post_switch_health_interval(),
        )
        if healthy:
            self._last_health_success_at = time.monotonic()
        return healthy

    def _verify_runtime_commit(self, service: str, expected_sha: str) -> bool:
        container_name = self._get_container_name(service)
        marker_path = f"/app/{self._runtime_marker_filename}"
        result = self.shell.run(["docker", "exec", container_name, "cat", marker_path])

        if result.returncode != 0:
            self.console.print(
                f"  [yellow]Runtime verification marker not readable:[/yellow] {marker_path} in {container_name}"
            )
            return False

        actual_sha = result.stdout.strip()
        if actual_sha != expected_sha:
            self.console.print(
                f"  [yellow]Runtime SHA mismatch:[/yellow] expected {expected_sha[:8]}, got {actual_sha[:8] if actual_sha else 'none'}"
            )
            return False

        self.console.print(f"  [green]✓ runtime commit verified[/green] ({expected_sha[:8]})")
        return True

    def reload(self, repo: Path) -> bool:
        """
        In accelerator mode, reload is just switching to current commit.
        """
        if self._current_sha:
            return self.switch_commit(self._current_sha, repo)
        return super().reload(repo)

    def stop(self, repo: Path) -> None:
        """
        In accelerator mode with --keep-alive flag, don't stop.
        Otherwise, normal shutdown.
        """
        if getattr(self.config, 'keep_alive', False):
            self.console.print("  [dim]Accelerator mode: keeping infrastructure alive[/dim]")
            return

        super().stop(repo)

    def setup_mount_compose(self, repo: Path, compose_file: Path) -> Path:
        """
        Create modified compose file that uses bind mount for code.
        This allows instant code swapping without container recreation.
        """
        # Read original compose
        import yaml
        compose_data = yaml.safe_load(compose_file.read_text())

        service = self.config.app_service or "backend"

        # Add bind mount for active worktree
        active_link = str(self.worktrees.base_dir / "active")

        if "services" not in compose_data:
            compose_data["services"] = {}

        if service in compose_data["services"]:
            service_config = compose_data["services"][service]

            # Add or modify volumes
            if "volumes" not in service_config:
                service_config["volumes"] = []

            # Add bind mount - will be updated via symlink
            service_config["volumes"].append(f"{active_link}:/app:rw")

            # Ensure service has restart policy for resilience
            service_config["restart"] = "unless-stopped"

        # Write modified compose
        modified_path = compose_file.parent / "docker-compose.rebuild.yml"
        modified_path.write_text(yaml.dump(compose_data, default_flow_style=False))

        return modified_path if service in compose_data["services"] else compose_file

    def _set_active_path(self, code_path: Path) -> Path:
        active_link = self.worktrees.base_dir / "active"
        active_link.parent.mkdir(parents=True, exist_ok=True)
        if active_link.exists() or active_link.is_symlink():
            active_link.unlink()
        active_link.symlink_to(code_path, target_is_directory=True)
        return active_link
