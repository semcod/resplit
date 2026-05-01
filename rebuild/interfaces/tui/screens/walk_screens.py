from __future__ import annotations

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
    from textual.widgets import Button, Footer, Header, Input, Label, Log, Select, Switch

    class WalkConfigScreen(Screen):
        """Formularz konfiguracji walk."""

        def __init__(self, repo: Path) -> None:
            super().__init__()
            self._repo = repo

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Label(f"⚙  Konfiguracja walk — {self._repo}", id="title")
            yield Label("Ile dni wstecz:", classes="section-label")
            yield Input("30", id="days-input")
            yield Label("Metoda deploy:", classes="section-label")
            yield Select(
                [
                    ("auto (wykryj z repo)", "auto"),
                    ("docker-compose", "docker-compose"),
                    ("uvicorn", "uvicorn"),
                    ("none (tylko skanuj)", "none"),
                ],
                id="deploy-select", value="auto",
            )
            yield Label("Health URL:", classes="section-label")
            yield Input("http://localhost:8003/api/health", id="health-url-input")
            yield Label("Base URL:", classes="section-label")
            yield Input("http://localhost:8003", id="base-url-input")
            yield Label("Katalog wyników:", classes="section-label")
            yield Input(".rebuild", id="output-input")
            yield Horizontal(
                Label("Screenshots (wymaga playwright):", classes="section-label"),
                Switch(value=False, id="screenshots-switch"),
                id="screenshots-row",
            )
            yield Horizontal(
                Label("Dry-run (bez deploy):", classes="section-label"),
                Switch(value=False, id="dryrun-switch"),
                id="dryrun-row",
            )
            yield Horizontal(
                Button("◀ Wstecz", id="btn-back", variant="default"),
                Button("▶ Uruchom walk", id="btn-run", variant="success"),
                id="action-row",
            )
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "btn-back":
                self.app.pop_screen()
            elif event.button.id == "btn-run":
                self._run_walk()

        def _run_walk(self) -> None:
            def _v(id_: str) -> str:
                return self.query_one(f"#{id_}", Input).value.strip()

            days = _v("days-input") or "30"
            deploy = self.query_one("#deploy-select", Select).value or "auto"
            health_url = _v("health-url-input")
            base_url = _v("base-url-input")
            output = _v("output-input") or ".rebuild"
            screenshots = self.query_one("#screenshots-switch", Switch).value
            dry_run = self.query_one("#dryrun-switch", Switch).value

            self.app.push_screen(WalkProgressScreen(
                repo=self._repo, days=int(days), deploy=deploy,
                health_url=health_url, base_url=base_url,
                output=Path(output), screenshots=screenshots, dry_run=dry_run,
            ))

    class WalkProgressScreen(Screen):
        """Live progress walk — subprocess rebuild walk."""

        BINDINGS = [Binding("ctrl+c", "cancel", "Cancel")]

        def __init__(self, repo: Path, days: int, deploy: str,
                     health_url: str, base_url: str, output: Path,
                     screenshots: bool, dry_run: bool) -> None:
            super().__init__()
            self._repo = repo
            self._days = days
            self._deploy = deploy
            self._health_url = health_url
            self._base_url = base_url
            self._output = output
            self._screenshots = screenshots
            self._dry_run = dry_run
            self._proc: Optional[subprocess.Popen] = None

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Label(f"▶  rebuild walk — {self._repo}", id="title")
            yield Log(id="walk-log", highlight=True)
            yield Horizontal(
                Button("✓ Przejdź do historii", id="btn-history", variant="success", disabled=True),
                Button("✗ Anuluj", id="btn-cancel", variant="error"),
                id="action-row",
            )
            yield Footer()

        def on_mount(self) -> None:
            self.set_interval(0.1, self._poll_output)
            self._start_walk()

        def _start_walk(self) -> None:
            cmd = [
                sys.executable, "-m", "rebuild",
                "walk", str(self._repo),
                "--days", str(self._days),
                "--deploy", self._deploy,
                "--health-url", self._health_url,
                "--base-url", self._base_url,
                "--output", str(self._output),
            ]
            if self._dry_run:
                cmd.append("--dry-run")
            if not self._screenshots:
                cmd.append("--no-screenshots")

            log = self.query_one("#walk-log", Log)
            log.write_line(f"$ {' '.join(cmd)}\n")

            try:
                self._proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
            except Exception as exc:
                log.write_line(f"[ERROR] {exc}")

        def _poll_output(self) -> None:
            if self._proc is None:
                return
            line = self._proc.stdout.readline()
            if line:
                self.query_one("#walk-log", Log).write_line(line.rstrip())
            if self._proc.poll() is not None:
                rc = self._proc.returncode
                self.query_one("#walk-log", Log).write_line(
                    f"\n[{'green' if rc == 0 else 'red'}]Exit: {rc}[/]"
                )
                self.query_one("#btn-history", Button).disabled = False
                self.set_interval(0.1, self._poll_output)

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "btn-history":
                from .history_screen import HistoryScreen
                self.app.push_screen(HistoryScreen(repo=self._repo, results_dir=self._output))
            elif event.button.id == "btn-cancel":
                if self._proc:
                    self._proc.terminate()
                self.app.pop_screen()

        def action_cancel(self) -> None:
            if self._proc:
                self._proc.terminate()
            self.app.pop_screen()
