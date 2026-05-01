from __future__ import annotations

from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.table import Table

from ...domain.day_result import DayResult


def print_report_links(output: Path, port: Optional[int], console: Console) -> None:
    base = f"http://localhost:{port}" if port else str(output.resolve())
    console.print("")
    console.print(f"  [bold cyan]Timeline:[/bold cyan]   {base}/index.html")
    console.print(f"  [bold cyan]Dashboard:[/bold cyan]  {base}/dashboard.html")
    console.print(f"  [dim]Per-day:     {base}/YYYY-MM-DD/report.html[/dim]")


def print_summary_table(results: List[DayResult], console: Console) -> None:
    table = Table(title="Podsumowanie walk", show_header=True)
    table.add_column("Dzień", style="bold")
    table.add_column("Commit")
    table.add_column("Health", justify="right")
    table.add_column("OK/Total", justify="right")
    table.add_column("Deploy")
    table.add_column("Czas")

    for r in sorted(results, key=lambda x: x.day):
        color = "green" if r.health_pct >= 80 else "yellow" if r.health_pct >= 50 else "red"
        table.add_row(
            str(r.day),
            r.commit.sha[:8] if r.commit else "—",
            f"[{color}]{r.health_pct}%[/{color}]",
            f"{r.ok_count}/{len(r.endpoints)}",
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
