"""
rebuild CLI — główny punkt wejścia.

Komendy:
  rebuild walk    — przejdź historię git i testuj endpointy
  rebuild restore — przywróć działający endpoint jako projekt
  rebuild report  — wygeneruj zbiorczy raport z istniejących wyników
  rebuild status  — pokaż status ostatniego walk
"""
from __future__ import annotations

import time
from datetime import date
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from ..domain.models import DeployMethod, WalkConfig
from ..domain.day_result import DayResult
from ..domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from ..application.pipeline import Pipeline

app = typer.Typer(
    name="rebuild",
    help="Historical deployment analysis — walk git history, test endpoints, capture screenshots.",
    rich_markup_mode="markdown",
    no_args_is_help=True,
)
console = Console()


# ──────────────────────────────────────────────
# walk
# ──────────────────────────────────────────────

@app.command()
def walk(
    repo: Path = typer.Argument(Path("."), help="Ścieżka do repozytorium"),
    days: int = typer.Option(30, help="Ile dni wstecz"),
    date_from: Optional[str] = typer.Option(None, "--from", help="Data od YYYY-MM-DD"),
    date_to: Optional[str] = typer.Option(None, "--to", help="Data do YYYY-MM-DD"),
    output: Path = typer.Option(Path(".rebuild"), help="Katalog wyjściowy"),
    deploy: str = typer.Option("auto", help="Metoda deploy: auto|docker-compose|uvicorn|none"),
    health_url: str = typer.Option("http://localhost:8003/api/health", help="URL health check"),
    base_url: str = typer.Option("http://localhost:8003", help="Bazowy URL usługi"),
    screenshots: bool = typer.Option(True, help="Rób zrzuty ekranu (wymaga playwright)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Tylko skanuj, bez deploy"),
) -> None:
    """Przejdź historię git dzień po dniu, deployuj i testuj endpointy."""
    from ..deployer import detect_deploy_method

    repo = repo.resolve()
    if not (repo / ".git").exists():
        console.print(f"[red]✗ {repo} nie jest repozytorium git[/red]")
        raise typer.Exit(1)

    # Wykrywanie metody deploy
    if deploy == "auto":
        method = detect_deploy_method(repo) if not dry_run else DeployMethod.NONE
    else:
        method = DeployMethod(deploy)

    config = WalkConfig(
        repo_path=repo,
        output_dir=output,
        days=days,
        date_from=date.fromisoformat(date_from) if date_from else None,
        date_to=date.fromisoformat(date_to) if date_to else None,
        deploy_method=method,
        health_url=health_url,
        base_url=base_url,
        screenshots=screenshots,
        dry_run=dry_run,
    )

    console.print(f"\n[bold]rebuild walk[/bold] v{__version__}")
    console.print(f"  repo:   {repo}")
    console.print(f"  output: {output}")
    console.print(f"  deploy: {method.value}")
    console.print(f"  days:   {days}\n")

    pipeline = Pipeline(config, console=console)
    all_results = pipeline.run()

    if all_results:
        console.print(f"\n[bold green]✓ Gotowe![/bold green]  Raport: {output / 'index.html'}")
        _print_summary_table(all_results)
    else:
        console.print("[yellow]Brak wyników do wyświetlenia.[/yellow]")


# ──────────────────────────────────────────────
# restore
# ──────────────────────────────────────────────

@app.command()
def restore(
    endpoint: str = typer.Argument(help="Ścieżka endpointu np. /api/health"),
    repo: Path = typer.Argument(Path("."), help="Repozytorium"),
    output: Path = typer.Option(Path("restored"), help="Katalog docelowy projektu"),
    results_dir: Path = typer.Option(Path(".rebuild"), help="Katalog z wynikami walk"),
) -> None:
    """Przywróć działający endpoint jako izolowany projekt."""
    from ..restorer import find_last_working_day, extract_endpoint

    day = find_last_working_day(endpoint, results_dir)
    if not day:
        console.print(f"[red]✗ Nie znaleziono działającego dnia dla {endpoint}[/red]")
        raise typer.Exit(1)

    console.print(f"Ostatni działający dzień: [bold]{day}[/bold]")
    target = output / endpoint.strip("/").replace("/", "-")
    extract_endpoint(repo, endpoint, day, target)
    console.print(f"[green]✓ Przywrócono do: {target}[/green]")


# ──────────────────────────────────────────────
# report
# ──────────────────────────────────────────────

@app.command()
def report(
    results_dir: Path = typer.Option(Path(".rebuild"), help="Katalog z wynikami walk"),
) -> None:
    """Wygeneruj zbiorczy raport z istniejących wyników."""
    import json
    from ..reporter import save_timeline_index

    all_results = []
    for day_dir in sorted(results_dir.iterdir()):
        rf = day_dir / "results.json"
        if not rf.exists():
            continue
        try:
            day_date = date.fromisoformat(day_dir.name)
        except ValueError:
            continue
        
        from ..domain.commit import CommitInfo
        commit_file = day_dir / "commit.txt"
        commit = None
        if commit_file.exists():
            lines = commit_file.read_text().splitlines()
            if lines:
                from datetime import datetime
                commit = CommitInfo(
                    sha=lines[0] if len(lines) > 0 else "",
                    message=lines[1] if len(lines) > 1 else "",
                    author=lines[2] if len(lines) > 2 else "",
                    timestamp=datetime.fromisoformat(lines[3]) if len(lines) > 3 else datetime.now(),
                    date=day_date,
                )
        data = json.loads(rf.read_text())
        endpoints = []
        ep_results = []
        for r in data:
            ep = Endpoint(method=r["method"], path=r["path"], base_url="")
            endpoints.append(ep)
            ep_results.append(EndpointResult(
                endpoint=ep,
                status=EndpointStatus(r["status"]),
                http_status=r.get("http_status"),
            ))
        result = DayResult(
            day=day_date,
            commit=commit,
            deploy_method=DeployMethod.NONE,
            deploy_success=True,
            endpoints=endpoints,
            endpoint_results=ep_results,
            output_dir=day_dir,
        )
        all_results.append(result)

    save_timeline_index(all_results, results_dir)
    console.print(f"[green]✓ Wygenerowano: {results_dir / 'index.html'}[/green]")


# ──────────────────────────────────────────────
# version
# ──────────────────────────────────────────────

@app.command()
def version() -> None:
    """Pokaż wersję rebuild."""
    console.print(f"rebuild v{__version__}")


# ──────────────────────────────────────────────
# dashboard
# ──────────────────────────────────────────────

@app.command()
def dashboard(
    results_dir: Path = typer.Option(Path(".rebuild"), help="Katalog z wynikami walk"),
    repo: Optional[Path] = typer.Option(None, help="Repo do pobrania CC (opcjonalnie)"),
) -> None:
    """Wygeneruj dashboard porównawczy: timeline health% + CC."""
    import json as _json
    from .dashboard import generate_dashboard

    all_results = []
    for day_dir in sorted(results_dir.iterdir()):
        rf = day_dir / "results.json"
        if not rf.exists():
            continue
        try:
            day_date = date.fromisoformat(day_dir.name)
        except ValueError:
            continue
        data = _json.loads(rf.read_text())
        ep_results = []
        endpoints = []
        for r in data:
            ep = Endpoint(method=r["method"], path=r["path"], base_url="")
            endpoints.append(ep)
            ep_results.append(EndpointResult(
                endpoint=ep,
                status=EndpointStatus(r["status"]),
                http_status=r.get("http_status"),
            ))
        all_results.append(DayResult(
            day=day_date,
            commit=None,
            deploy_method=DeployMethod.NONE,
            deploy_success=True,
            endpoints=endpoints,
            endpoint_results=ep_results,
            output_dir=day_dir,
        ))

    if not all_results:
        console.print("[yellow]Brak wyników w katalogu.[/yellow]")
        raise typer.Exit(0)

    out = generate_dashboard(all_results, results_dir, repo=repo)
    console.print(f"[green]✓ Dashboard: {out}[/green]")


# ──────────────────────────────────────────────
# tui
# ──────────────────────────────────────────────

@app.command()
def tui() -> None:
    """Interaktywne menu TUI: wybór projektu → walk → historia → diff → restore."""
    from .tui import launch_tui
    launch_tui()


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _print_summary_table(results: list[DayResult]) -> None:
    table = Table(title="Podsumowanie walk", show_header=True)
    table.add_column("Dzień", style="bold")
    table.add_column("Commit")
    table.add_column("Health", justify="right")
    table.add_column("OK/Total", justify="right")
    table.add_column("Deploy")

    for r in sorted(results, key=lambda x: x.day):
        color = "green" if r.health_pct >= 80 else "yellow" if r.health_pct >= 50 else "red"
        table.add_row(
            str(r.day),
            r.commit.sha[:8] if r.commit else "—",
            f"[{color}]{r.health_pct}%[/{color}]",
            f"{r.ok_count}/{len(r.endpoints)}",
            "✓" if r.deploy_success else "✗",
        )

    console.print(table)
