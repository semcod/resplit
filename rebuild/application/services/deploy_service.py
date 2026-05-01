from __future__ import annotations
import time
import hashlib
from pathlib import Path
from typing import Optional, List, Any

from rich.console import Console

from ...domain.models import DeployMethod, WalkConfig
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

        if method == DeployMethod.DOCKER_COMPOSE:
            return self._compose_up(repo)
        if method == DeployMethod.UVICORN:
            return self._uvicorn_start(repo)
        return False

    def reload(self, repo: Path) -> bool:
        """
        Performs a fast reload of the application in Replay Mode.
        Restarts only the specified app service.
        """
        if self.config.deploy_method != DeployMethod.DOCKER_COMPOSE:
            return self.start(repo)

        service = self.config.app_service or "backend"
        self.console.print(f"  [bold cyan]docker compose restart {service}[/bold cyan]")
        cf = self._compose_file(repo)
        cmd = ["docker", "compose", "-p", self._project_name, "-f", str(cf), "restart", service]
        result = self.shell.run(cmd, cwd=repo)
        
        if result.returncode != 0:
            self.console.print(f"  [red]Restart failed:[/red] {result.stderr[:200]}")
            return False
            
        return self._wait_healthy()

    def stop(self, repo: Path) -> None:
        if self.config.dry_run or self.config.deploy_method == DeployMethod.NONE:
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
        if result.returncode != 0:
            self.console.print(f"  [red]docker compose up failed:[/red]\n{result.stderr[:500]}")
            return False
        return self._wait_healthy()

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
        return self._wait_healthy()

    def _uvicorn_stop(self) -> None:
        if self._uvicorn_proc:
            self._uvicorn_proc.terminate()
            self._uvicorn_proc = None

    def _wait_healthy(self) -> bool:
        deadline = time.time() + self.config.health_timeout
        while time.time() < deadline:
            try:
                r = self.http.get(self.config.health_url)
                if r.status_code < 500:
                    self.console.print(f"  [green]✓ healthy[/green] ({self.config.health_url})")
                    return True
            except Exception:
                pass
            time.sleep(self.config.health_interval)
        self.console.print(f"  [red]✗ health timeout ({self.config.health_timeout}s)[/red]")
        return False
