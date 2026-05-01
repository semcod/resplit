"""
rebuild.deployer — wykrywa metodę deployu i zarządza cyklem życia usługi.

Wspierane metody:
  - docker-compose (docker-compose.yml / docker compose)
  - uvicorn (FastAPI / wykryty server.py)
  - custom (komenda z rebuild.yaml)
  - none (dry-run / brak deployable artefaktów)
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console

from .domain.models import DeployMethod, WalkConfig

console = Console()


# ──────────────────────────────────────────────
# Detekcja
# ──────────────────────────────────────────────

def detect_deploy_method(repo: Path) -> DeployMethod:
    """Automatycznie wykrywa metodę deployu na podstawie plików w repo."""
    if (repo / "docker-compose.yml").exists() or (repo / "docker-compose.yaml").exists():
        return DeployMethod.DOCKER_COMPOSE
    if (repo / "backend" / "server.py").exists() or (repo / "server.py").exists():
        return DeployMethod.UVICORN
    return DeployMethod.NONE


def _compose_file(repo: Path, config: WalkConfig) -> Path:
    explicit = repo / config.compose_file
    if explicit.exists():
        return explicit
    for name in ("docker-compose.yml", "docker-compose.yaml"):
        p = repo / name
        if p.exists():
            return p
    raise FileNotFoundError(f"Nie znaleziono pliku docker-compose w {repo}")


# ──────────────────────────────────────────────
# Start / stop
# ──────────────────────────────────────────────

def start(repo: Path, config: WalkConfig) -> bool:
    """Uruchamia usługę. Zwraca True jeśli sukces."""
    method = config.deploy_method
    if method == DeployMethod.NONE:
        return True  # dry-run / brak usługi

    if config.dry_run:
        console.print(f"[dim]  [dry-run] skipped deploy ({method})[/dim]")
        return True

    if method == DeployMethod.DOCKER_COMPOSE:
        return _compose_up(repo, config)
    if method == DeployMethod.UVICORN:
        return _uvicorn_start(repo, config)
    return False


def stop(repo: Path, config: WalkConfig) -> None:
    """Zatrzymuje usługę."""
    if config.dry_run or config.deploy_method == DeployMethod.NONE:
        return
    if config.deploy_method == DeployMethod.DOCKER_COMPOSE:
        _compose_down(repo, config)
    elif config.deploy_method == DeployMethod.UVICORN:
        _uvicorn_stop()


# ──────────────────────────────────────────────
# Docker Compose
# ──────────────────────────────────────────────

_compose_proc: Optional[subprocess.Popen] = None


def _compose_up(repo: Path, config: WalkConfig) -> bool:
    cf = _compose_file(repo, config)
    cmd = ["docker", "compose", "-f", str(cf), "up", "-d", "--build"]
    console.print(f"  [bold cyan]docker compose up[/bold cyan] ({cf.name})")
    result = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"  [red]docker compose up failed:[/red]\n{result.stderr[:500]}")
        return False
    return _wait_healthy(config)


def _compose_down(repo: Path, config: WalkConfig) -> None:
    try:
        cf = _compose_file(repo, config)
        cmd = ["docker", "compose", "-f", str(cf), "down", "--remove-orphans"]
        subprocess.run(cmd, cwd=repo, capture_output=True, timeout=60)
    except Exception as e:
        console.print(f"  [yellow]docker compose down error: {e}[/yellow]")


# ──────────────────────────────────────────────
# Uvicorn (FastAPI)
# ──────────────────────────────────────────────

_uvicorn_proc: Optional[subprocess.Popen] = None


def _uvicorn_start(repo: Path, config: WalkConfig) -> bool:
    global _uvicorn_proc
    server = repo / "backend" / "server.py"
    if not server.exists():
        server = repo / "server.py"
    module = "backend.server:app" if (repo / "backend" / "server.py").exists() else "server:app"
    cmd = ["uvicorn", module, "--host", "0.0.0.0", "--port", "8003", "--reload"]
    console.print(f"  [bold cyan]uvicorn[/bold cyan] {module}")
    _uvicorn_proc = subprocess.Popen(cmd, cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return _wait_healthy(config)


def _uvicorn_stop() -> None:
    global _uvicorn_proc
    if _uvicorn_proc:
        _uvicorn_proc.terminate()
        try:
            _uvicorn_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _uvicorn_proc.kill()
        _uvicorn_proc = None


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────

def _wait_healthy(config: WalkConfig) -> bool:
    """Czeka na odpowiedź health_url do health_timeout sekund."""
    deadline = time.time() + config.health_timeout
    while time.time() < deadline:
        try:
            r = httpx.get(config.health_url, timeout=3)
            if r.status_code < 500:
                console.print(f"  [green]✓ healthy[/green] ({config.health_url})")
                return True
        except Exception:
            pass
        time.sleep(config.health_interval)
    console.print(f"  [red]✗ health timeout ({config.health_timeout}s)[/red]")
    return False
