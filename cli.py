"""
retrodep CLI — główny punkt wejścia.

Komendy:
  retrodep walk    — przejdź historię git i testuj endpointy
  retrodep restore — przywróć działający endpoint jako projekt
  retrodep report  — wygeneruj zbiorczy raport z istniejących wyników
  retrodep status  — pokaż status ostatniego walk
"""
from __future__ import annotations

import time
from datetime import date
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .deployer import detect_deploy_method, start, stop
from .endpoint_scanner import scan_endpoints
from .git_walker import checkout, days_with_commits, restore_head
from .models import (
    DeployMethod,
    DayResult,
    EndpointResult,
    EndpointStatus,
    WalkConfig,
)
from .reporter import save_day, save_timeline_index

app = typer.Typer(
    name="retrodep",
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
    output: Path = typer.Option(Path(".retrodep"), help="Katalog wyjściowy"),
    deploy: str = typer.Option("auto", help="Metoda deploy: auto|docker-compose|uvicorn|none"),
    health_url: str = typer.Option("http://localhost:8003/api/health", help="URL health check"),
    base_url: str = typer.Option("http://localhost:8003", help="Bazowy URL usługi"),
    screenshots: bool = typer.Option(True, help="Rób zrzuty ekranu (wymaga playwright)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Tylko skanuj, bez deploy"),
) -> None:
    """Przejdź historię git dzień po dniu, deployuj i testuj endpointy."""

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

    console.print(f"\n[bold]retrodep walk[/bold] v{__version__}")
    console.print(f"  repo:   {repo}")
    console.print(f"  output: {output}")
    console.print(f"  deploy: {method.value}")
    console.print(f"  days:   {days}\n")

    commits = days_with_commits(config)
    if not commits:
        console.print("[yellow]Brak commitów w podanym przedziale.[/yellow]")
        raise typer.Exit(0)

    console.print(f"Znaleziono [bold]{len(commits)}[/bold] dni z commitami.\n")

    all_results: list[DayResult] = []

    for day, commit in commits:
        day_dir = output / str(day)
        console.rule(f"[bold]{day}[/bold]  {commit.sha[:8]}  {commit.message[:60]}")

        t0 = time.time()
        result = DayResult(
            day=day,
            commit=commit,
            deploy_method=method,
            deploy_success=False,
            output_dir=day_dir,
        )

        try:
            # 1. Checkout
            if not dry_run:
                checkout(repo, commit.sha)

            # 2. Deploy
            result.deploy_success = start(repo, config)
            if not result.deploy_success and not dry_run:
                console.print("  [red]✗ deploy failed — skip endpoints[/red]")
                result.duration_seconds = time.time() - t0
                save_day(result)
                all_results.append(result)
                stop(repo, config)
                continue

            # 3. Skanuj endpointy
            result.endpoints = scan_endpoints(repo, config)
            console.print(f"  Endpointów: [bold]{len(result.endpoints)}[/bold]")

            # 4. Testuj każdy endpoint
            result.endpoint_results = _probe_endpoints(result, config, day_dir)

            # 5. Raport
            save_day(result)

        except KeyboardInterrupt:
            console.print("\n[yellow]Przerwano przez użytkownika.[/yellow]")
            break
        except Exception as exc:
            result.error = str(exc)
            console.print(f"  [red]Błąd: {exc}[/red]")
        finally:
            # 6. Cleanup
            stop(repo, config)
            result.duration_seconds = time.time() - t0

        all_results.append(result)
        _print_day_summary(result)

    # Przywróć HEAD
    if not dry_run:
        restore_head(repo)

    # Zbiorczy index
    save_timeline_index(all_results, output)

    console.print(f"\n[bold green]✓ Gotowe![/bold green]  Raport: {output / 'index.html'}")
    _print_summary_table(all_results)


# ──────────────────────────────────────────────
# restore
# ──────────────────────────────────────────────

@app.command()
def restore(
    endpoint: str = typer.Argument(help="Ścieżka endpointu np. /api/health"),
    repo: Path = typer.Argument(Path("."), help="Repozytorium"),
    output: Path = typer.Option(Path("restored"), help="Katalog docelowy projektu"),
    results_dir: Path = typer.Option(Path(".retrodep"), help="Katalog z wynikami walk"),
) -> None:
    """Przywróć działający endpoint jako izolowany projekt."""
    from .restorer import find_last_working_day, extract_endpoint

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
    results_dir: Path = typer.Option(Path(".retrodep"), help="Katalog z wynikami walk"),
) -> None:
    """Wygeneruj zbiorczy raport z istniejących wyników."""
    import json

    all_results = []
    for day_dir in sorted(results_dir.iterdir()):
        rf = day_dir / "results.json"
        if not rf.exists():
            continue
        # Uproszczona rekonstrukcja DayResult tylko do indeksu
        try:
            day_date = date.fromisoformat(day_dir.name)
        except ValueError:
            continue
        from .models import CommitInfo
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
        ok = sum(1 for r in data if r["status"] == "ok")
        total = len(data)
        from .models import Endpoint, EndpointResult, EndpointStatus
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
    """Pokaż wersję retrodep."""
    console.print(f"retrodep v{__version__}")


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _probe_endpoints(result: DayResult, config: WalkConfig, day_dir: Path) -> list[EndpointResult]:
    """Testuje każdy endpoint HTTP (GET) i opcjonalnie robi screenshot."""
    ep_results = []

    screenshots_dir = day_dir / "screenshots"
    if config.screenshots:
        screenshots_dir.mkdir(parents=True, exist_ok=True)

    for ep in result.endpoints:
        if ep.method != "GET":
            # Non-GET: zapisz jako SKIP
            ep_results.append(EndpointResult(endpoint=ep, status=EndpointStatus.SKIP))
            continue

        t0 = time.time()
        try:
            r = httpx.get(ep.url, timeout=8, follow_redirects=True)
            ms = (time.time() - t0) * 1000
            status = EndpointStatus.OK if r.status_code < 400 else EndpointStatus.FAIL
            screenshot_path = None
            if config.screenshots:
                screenshot_path = _take_screenshot(ep.url, screenshots_dir / f"{ep.slug}.png")
            ep_results.append(EndpointResult(
                endpoint=ep,
                status=status,
                http_status=r.status_code,
                response_time_ms=ms,
                screenshot_path=screenshot_path,
            ))
        except httpx.TimeoutException:
            ep_results.append(EndpointResult(endpoint=ep, status=EndpointStatus.TIMEOUT))
        except Exception as exc:
            ep_results.append(EndpointResult(endpoint=ep, status=EndpointStatus.FAIL, error=str(exc)))

    return ep_results


def _take_screenshot(url: str, path: Path) -> Optional[Path]:
    """Screenshot via Playwright (jeśli zainstalowany)."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=15_000)
            page.screenshot(path=str(path), full_page=True)
            browser.close()
        return path
    except ImportError:
        return None
    except Exception:
        return None


def _print_day_summary(result: DayResult) -> None:
    color = "green" if result.health_pct >= 80 else "yellow" if result.health_pct >= 50 else "red"
    console.print(
        f"  [{color}]{result.health_pct}% health[/{color}]"
        f"  OK:{result.ok_count}  FAIL:{result.fail_count}"
        f"  ({result.duration_seconds:.1f}s)"
    )


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
