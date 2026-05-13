from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Optional, List

from click.core import ParameterSource
from rich.console import Console
from rich.table import Table

from ...domain.day_result import DayResult


def collect_cli_overrides(ctx: Any, names: Iterable[str]) -> Dict[str, bool]:
    """Build a ``{param_name: was_explicitly_passed_on_cli}`` mapping.

    Used by typer commands to distinguish CLI-provided values (which should
    override `rebuild.yaml`) from defaults (which should not).

    Replaces ~14 lines of duplicated ``ctx.get_parameter_source(...) ==
    ParameterSource.COMMANDLINE`` boilerplate per command.
    """
    return {name: ctx.get_parameter_source(name) == ParameterSource.COMMANDLINE for name in names}


def print_report_links(output: Path, port: Optional[int], console: Console) -> None:
    base = f"http://localhost:{port}" if port else str(output.resolve())
    console.print("")
    console.print(f"  [bold cyan]Timeline:[/bold cyan]   {base}/index.html")
    console.print(f"  [bold cyan]Dashboard:[/bold cyan]  {base}/dashboard.html")
    console.print(f"  [dim]Per-day:     {base}/YYYY-MM-DD/report.html[/dim]")


def compute_health_trend_labels(
    results: List[DayResult], regression_threshold: float = 20.0
) -> List[str]:
    # Delegated to the canonical implementation (Sprint 2 / 2026-05-07).
    # See `rebuild.application.services.regression_service` for details.
    from ...application.services.regression_service import (
        compute_health_trend_labels as _compute,
    )

    return _compute(results, regression_threshold)


def compute_endpoint_count_trend_labels(
    results: List[DayResult], warning_threshold_pct: float = 10.0
) -> List[str]:
    # Delegated to the canonical implementation (Sprint 5b / 2026-05-08).
    # See `rebuild.application.services.endpoint_trend_service` for details.
    from ...application.services.endpoint_trend_service import (
        compute_endpoint_count_trend_labels as _compute,
    )

    return _compute(results, warning_threshold_pct)


def print_summary_table(results: List[DayResult], console: Console) -> None:
    table = Table(title="Podsumowanie walk", show_header=True)
    table.add_column("Dzień", style="bold")
    table.add_column("Commit")
    table.add_column("Health", justify="right")
    table.add_column("Trend", justify="right")
    table.add_column("OK/Total", justify="right")
    table.add_column("EP Δ", justify="right")
    table.add_column("Deploy")
    table.add_column("Czas")

    ordered = sorted(results, key=lambda x: x.day)
    trends = compute_health_trend_labels(ordered)
    endpoint_trends = compute_endpoint_count_trend_labels(ordered)

    for r, trend, ep_trend in zip(ordered, trends, endpoint_trends):
        color = "green" if r.health_pct >= 80 else "yellow" if r.health_pct >= 50 else "red"
        trend_cell = (
            f"[red]{trend}[/red]"
            if trend.startswith("⚠")
            else f"[green]{trend}[/green]"
            if trend.startswith("+")
            else f"[dim]{trend}[/dim]"
        )
        ep_trend_cell = (
            f"[yellow]{ep_trend}[/yellow]" if ep_trend.startswith("⚠") else f"[dim]{ep_trend}[/dim]"
        )
        table.add_row(
            str(r.day),
            r.commit.sha[:8] if r.commit else "—",
            f"[{color}]{r.health_pct}%[/{color}]",
            trend_cell,
            f"{r.ok_count}/{len(r.endpoints)}",
            ep_trend_cell,
            "✓" if r.deploy_success else "✗",
            f"{r.duration_seconds:.2f}s",
        )
    console.print(table)


def serve_reports(output: Path, port: int, console: Console) -> None:
    import http.server
    import socketserver
    import threading
    import webbrowser
    import os
    import queue
    from ...application.services.event_service import get_event_service

    os.chdir(output)
    event_service = get_event_service()
    event_service.enable()

    class SSEHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path == "/events":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                q = event_service.subscribe()
                try:
                    while True:
                        event = q.get(timeout=30)
                        self.wfile.write(event.encode())
                        self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b"data: keepalive\n\n")
                    self.wfile.flush()
                except Exception:
                    pass
                finally:
                    event_service.unsubscribe(q)
            else:
                super().do_GET()

    SSEHandler.log_message = lambda *a: None

    with socketserver.TCPServer(("", port), SSEHandler) as httpd:
        url = f"http://localhost:{port}/index.html"
        console.print(f"\n[bold green]Serwer HTTP uruchomiony:[/bold green] {url}")
        console.print(f"  [dim]SSE endpoint:[/dim] http://localhost:{port}/events")
        console.print("  [dim]Ctrl+C aby zatrzymać[/dim]\n")
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            console.print("\n[dim]Serwer zatrzymany.[/dim]")
            event_service.disable()
