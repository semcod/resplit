from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from ..compat import TEXTUAL_OK

if TEXTUAL_OK:
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal
    from textual.screen import Screen
    from textual.widgets import Button, Footer, Header, Input, Label, Log, Select

    class RestoreScreen(Screen):
        """Restore endpoint jako izolowany projekt Docker z podanym URL/portem."""

        BINDINGS = [Binding("escape", "pop_screen", "Wstecz")]

        def __init__(
            self, repo: Path, results_dir: Path,
            preselect_day: str = "", preselect_endpoint: str = "",
            day_data: Optional[dict] = None,
        ) -> None:
            super().__init__()
            self._repo = repo
            self._results_dir = results_dir
            self._preselect_day = preselect_day
            self._preselect_endpoint = preselect_endpoint
            self._day_data = day_data

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Label("🔧 Restore endpoint → izolowany projekt Docker", id="title")

            endpoints = []
            if self._day_data:
                endpoints = [r.get("path", "") for r in self._day_data.get("results", []) if r.get("path")]

            yield Label("Ścieżka endpointu:", classes="section-label")
            if endpoints:
                yield Select(
                    [(ep, ep) for ep in endpoints], id="endpoint-select",
                    value=self._preselect_endpoint or endpoints[0],
                )
            else:
                yield Input(value=self._preselect_endpoint or "/api/health", id="endpoint-input")

            yield Label("Katalog wyjściowy:", classes="section-label")
            yield Input("./restored", id="output-input")
            yield Label("Port dla odtworzonej usługi Docker:", classes="section-label")
            yield Input("8099", id="port-input")
            yield Label("Wyniki walk (results-dir):", classes="section-label")
            yield Input(str(self._results_dir), id="results-dir-input")

            yield Log(id="restore-log", highlight=True)
            yield Label("", id="restore-status")

            yield Horizontal(
                Button("◀ Wstecz", id="btn-back", variant="default"),
                Button("🔧 Restore", id="btn-restore", variant="warning"),
                Button("🐳 Uruchom Docker", id="btn-docker", variant="success", disabled=True),
                id="action-row",
            )
            yield Footer()

        def _get_endpoint(self) -> str:
            try:
                return self.query_one("#endpoint-select", Select).value or "/api/health"
            except Exception:
                try:
                    return self.query_one("#endpoint-input", Input).value or "/api/health"
                except Exception:
                    return "/api/health"

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "btn-back":
                self.app.pop_screen()
            elif event.button.id == "btn-restore":
                self._run_restore()
            elif event.button.id == "btn-docker":
                self._run_docker()

        def _run_restore(self) -> None:
            endpoint = self._get_endpoint()
            output = self.query_one("#output-input", Input).value or "./restored"
            port = self.query_one("#port-input", Input).value or "8099"
            results_dir = self.query_one("#results-dir-input", Input).value or str(self._results_dir)
            log = self.query_one("#restore-log", Log)

            cmd = [
                sys.executable, "-m", "rebuild",
                "restore", endpoint, str(self._repo),
                "--output", output, "--results-dir", results_dir,
            ]
            log.write_line(f"$ {' '.join(cmd)}\n")

            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in proc.stdout:
                    log.write_line(line.rstrip())
                rc = proc.wait()
                status = self.query_one("#restore-status", Label)
                if rc == 0:
                    slug = endpoint.lstrip("/").replace("/", "-")
                    target = Path(output) / slug
                    status.update(f"[green]✓ Przywrócono do {target}[/green]  Port Docker: {port}")
                    self._patch_docker_port(target, port)
                    self.query_one("#btn-docker", Button).disabled = False
                    self._last_target = target
                    self._last_port = port
                else:
                    status.update(f"[red]✗ Błąd (exit {rc})[/red]")
            except Exception as exc:
                log.write_line(f"[ERROR] {exc}")

        def _patch_docker_port(self, target: Path, port: str) -> None:
            dc = target / "docker" / "docker-compose.yml"
            if not dc.exists():
                return
            content = re.sub(r'"?\d{4,5}:(\d{4,5})"?', f'"{port}:\\1"', dc.read_text())
            dc.write_text(content)

        def _run_docker(self) -> None:
            target = getattr(self, "_last_target", None)
            port = getattr(self, "_last_port", "8099")
            if not target:
                return
            dc_dir = target / "docker" if (target / "docker").exists() else target
            log = self.query_one("#restore-log", Log)
            cmd = ["docker", "compose", "up", "-d"]
            log.write_line(f"\n$ cd {dc_dir} && {' '.join(cmd)}\n")
            try:
                proc = subprocess.Popen(
                    cmd, cwd=dc_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                )
                for line in proc.stdout:
                    log.write_line(line.rstrip())
                rc = proc.wait()
                status = self.query_one("#restore-status", Label)
                if rc == 0:
                    url = f"http://localhost:{port}{self._get_endpoint()}"
                    status.update(f"[green]🐳 Uruchomiono!  URL: {url}[/green]")
                else:
                    status.update(f"[red]✗ docker compose up failed (exit {rc})[/red]")
            except FileNotFoundError:
                log.write_line("[ERROR] docker nie znaleziony — zainstaluj Docker Desktop")
