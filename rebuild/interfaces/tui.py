"""
rebuild.tui — interaktywne menu terminalowe (Textual).

Przepływ:
  1. Wybór projektu (repo)
  2. Konfiguracja walk (days, deploy method, URLs)
  3. Uruchomienie walk z live progress
  4. Przeglądanie historii dzień po dniu
  5. Diff endpointów: co pojawiło się / zniknęło / zmieniło status
  6. Restore: wybrany endpoint → izolowany projekt Docker z konkretnym URL

Wymaga: pip install "textual>=0.60"
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Optional

# ──────────────────────────────────────────────
# Graceful import
# ──────────────────────────────────────────────

try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
    from textual.screen import ModalScreen, Screen
    from textual.widgets import (
        Button,
        DataTable,
        Footer,
        Header,
        Input,
        Label,
        ListItem,
        ListView,
        Log,
        Markdown,
        ProgressBar,
        Select,
        Static,
        Switch,
    )
    _TEXTUAL_OK = True
except ImportError:
    _TEXTUAL_OK = False


# ──────────────────────────────────────────────
# Data helpers
# ──────────────────────────────────────────────

def _load_day_results(results_dir: Path) -> list[dict]:
    """Wczytuje wyniki ze wszystkich podkatalogów .rebuild/YYYY-MM-DD/."""
    days = []
    for d in sorted(results_dir.iterdir()):
        rf = d / "results.json"
        if not d.is_dir() or not rf.exists():
            continue
        try:
            date.fromisoformat(d.name)
        except ValueError:
            continue
        try:
            results = json.loads(rf.read_text())
        except (json.JSONDecodeError, OSError):
            results = []
        commit_txt = (d / "commit.txt").read_text().strip() if (d / "commit.txt").exists() else ""
        days.append({
            "day": d.name,
            "results": results,
            "commit": commit_txt.split("\n")[0][:50] if commit_txt else "—",
            "path": d,
        })
    return days


def _endpoint_diff(prev: list[dict], curr: list[dict]) -> list[dict]:
    """
    Porównuje dwie listy wyników endpointów (z results.json).
    Zwraca listę zmian: added / removed / status_changed.
    """
    prev_map = {(r["method"], r["path"]): r for r in prev}
    curr_map = {(r["method"], r["path"]): r for r in curr}

    changes = []
    for key, r in curr_map.items():
        if key not in prev_map:
            changes.append({**r, "change": "added"})
        elif prev_map[key]["status"] != r["status"]:
            changes.append({
                **r,
                "change": "status_changed",
                "prev_status": prev_map[key]["status"],
            })
    for key, r in prev_map.items():
        if key not in curr_map:
            changes.append({**r, "change": "removed"})

    return changes


def _health_bar(pct: float, width: int = 20) -> str:
    filled = int(pct / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
    return f"[{color}]{bar}[/{color}] {pct:.0f}%"


def _calc_health(results: list[dict]) -> float:
    if not results:
        return 0.0
    ok = sum(1 for r in results if r.get("status") == "ok")
    return round(ok / len(results) * 100, 1)


# ──────────────────────────────────────────────
# Screens
# ──────────────────────────────────────────────

if _TEXTUAL_OK:

    # ── Screen 1: wybór projektu ───────────────

    class ProjectScreen(Screen):
        """Wybór projektu (katalogu git)."""

        BINDINGS = [
            Binding("ctrl+c", "quit", "Quit"),
            Binding("f1", "help", "Help"),
        ]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Label("rebuild — Historical Deployment Analysis", id="title")
            yield Label("Wybierz katalog projektu (repo git):", classes="section-label")
            yield Horizontal(
                Input(
                    placeholder="/path/to/repo  lub  . dla bieżącego",
                    id="repo-input",
                ),
                Button("Browse recent", id="btn-browse", variant="default"),
                id="repo-row",
            )
            yield Label("Katalog wyników (.rebuild/):", classes="section-label")
            yield Input(
                placeholder=".rebuild  (domyślnie)",
                id="results-input",
            )
            yield Label("", id="repo-error", classes="error")
            yield Horizontal(
                Button("▶  Otwórz historię", id="btn-open-history", variant="success"),
                Button("⚙  Nowy walk", id="btn-new-walk", variant="primary"),
                id="action-row",
            )
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "btn-browse":
                self._populate_recent()
            elif event.button.id == "btn-open-history":
                self._open_history()
            elif event.button.id == "btn-new-walk":
                self._new_walk()

        def _repo_path(self) -> Path:
            val = self.query_one("#repo-input", Input).value.strip() or "."
            return Path(val).expanduser().resolve()

        def _results_dir(self) -> Path:
            val = self.query_one("#results-input", Input).value.strip()
            if val:
                return Path(val).expanduser()
            return self._repo_path() / ".rebuild"

        def _populate_recent(self) -> None:
            try:
                recent = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True, text=True, cwd=Path("."),
                )
                if recent.returncode == 0:
                    self.query_one("#repo-input", Input).value = recent.stdout.strip()
            except Exception:
                pass

        def _open_history(self) -> None:
            repo = self._repo_path()
            results_dir = self._results_dir()
            err = self.query_one("#repo-error", Label)
            if not results_dir.exists():
                err.update(f"⚠ Brak katalogu wyników: {results_dir}  →  uruchom najpierw 'rebuild walk'")
                return
            err.update("")
            self.app.push_screen(HistoryScreen(repo=repo, results_dir=results_dir))

        def _new_walk(self) -> None:
            repo = self._repo_path()
            err = self.query_one("#repo-error", Label)
            if not (repo / ".git").exists():
                err.update(f"⚠ Nie znaleziono repozytorium git: {repo}")
                return
            err.update("")
            self.app.push_screen(WalkConfigScreen(repo=repo))

        def action_help(self) -> None:
            self.app.push_screen(HelpScreen())


    # ── Screen 2: konfiguracja walk ────────────

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
                id="deploy-select",
                value="auto",
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
                repo=self._repo,
                days=int(days),
                deploy=deploy,
                health_url=health_url,
                base_url=base_url,
                output=Path(output),
                screenshots=screenshots,
                dry_run=dry_run,
            ))


    # ── Screen 3: progress walk ────────────────

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
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
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
                log = self.query_one("#walk-log", Log)
                log.write_line(f"\n[{'green' if rc == 0 else 'red'}]Exit: {rc}[/]")
                self.query_one("#btn-history", Button).disabled = False
                self.set_interval(0.1, self._poll_output)  # stop polling

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "btn-history":
                self.app.push_screen(HistoryScreen(
                    repo=self._repo,
                    results_dir=self._output,
                ))
            elif event.button.id == "btn-cancel":
                if self._proc:
                    self._proc.terminate()
                self.app.pop_screen()

        def action_cancel(self) -> None:
            if self._proc:
                self._proc.terminate()
            self.app.pop_screen()


    # ── Screen 4: historia dzień po dniu ──────

    class HistoryScreen(Screen):
        """
        Tabela: dzień | commit | endpointy | health% | diff vs poprzedni dzień.
        Wybór wiersza → szczegóły endpointów.
        """

        BINDINGS = [
            Binding("escape", "pop_screen", "Wstecz"),
            Binding("d", "show_diff", "Diff"),
            Binding("r", "restore", "Restore"),
        ]

        def __init__(self, repo: Path, results_dir: Path) -> None:
            super().__init__()
            self._repo = repo
            self._results_dir = results_dir
            self._days: list[dict] = []

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Label(f"📅 Historia — {self._results_dir}", id="title")
            yield DataTable(id="history-table", cursor_type="row")
            yield Static("", id="status-bar")
            yield Horizontal(
                Button("◀ Wstecz", id="btn-back", variant="default"),
                Button("🔍 Diff vs poprzedni", id="btn-diff", variant="primary"),
                Button("📋 Endpointy dnia", id="btn-endpoints", variant="default"),
                Button("🔧 Restore endpoint", id="btn-restore", variant="warning"),
                id="action-row",
            )
            yield Footer()

        def on_mount(self) -> None:
            self._days = _load_day_results(self._results_dir)
            table = self.query_one("#history-table", DataTable)
            table.add_columns("Dzień", "Commit", "#EP", "OK", "FAIL", "Health%", "Δ vs poprzedni")

            for i, d in enumerate(self._days):
                results = d["results"]
                health = _calc_health(results)
                ok = sum(1 for r in results if r.get("status") == "ok")
                fail = sum(1 for r in results if r.get("status") == "fail")
                total = len(results)

                if i > 0:
                    prev = self._days[i - 1]["results"]
                    changes = _endpoint_diff(prev, results)
                    if changes:
                        added = sum(1 for c in changes if c["change"] == "added")
                        removed = sum(1 for c in changes if c["change"] == "removed")
                        changed = sum(1 for c in changes if c["change"] == "status_changed")
                        delta = f"+{added} -{removed} ~{changed}"
                    else:
                        delta = "="
                else:
                    delta = "baseline"

                health_str = f"{health:.0f}%"
                if health >= 80:
                    health_str = f"[green]{health_str}[/green]"
                elif health >= 50:
                    health_str = f"[yellow]{health_str}[/yellow]"
                else:
                    health_str = f"[red]{health_str}[/red]"

                table.add_row(
                    d["day"],
                    d["commit"],
                    str(total),
                    f"[green]{ok}[/green]",
                    f"[red]{fail}[/red]",
                    health_str,
                    delta,
                )

            status = self.query_one("#status-bar", Static)
            status.update(f"{len(self._days)} dni  ·  [dim]D=diff  R=restore  Enter=endpointy[/dim]")

        def _selected_idx(self) -> int:
            table = self.query_one("#history-table", DataTable)
            return table.cursor_row

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "btn-back":
                self.app.pop_screen()
            elif event.button.id in ("btn-diff", "btn-endpoints"):
                idx = self._selected_idx()
                if 0 <= idx < len(self._days):
                    self.app.push_screen(EndpointDetailScreen(
                        day_data=self._days[idx],
                        prev_data=self._days[idx - 1] if idx > 0 else None,
                        show_diff=(event.button.id == "btn-diff"),
                    ))
            elif event.button.id == "btn-restore":
                self.action_restore()

        def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
            idx = event.cursor_row
            if 0 <= idx < len(self._days):
                self.app.push_screen(EndpointDetailScreen(
                    day_data=self._days[idx],
                    prev_data=self._days[idx - 1] if idx > 0 else None,
                    show_diff=False,
                ))

        def action_show_diff(self) -> None:
            idx = self._selected_idx()
            if 0 <= idx < len(self._days):
                self.app.push_screen(EndpointDetailScreen(
                    day_data=self._days[idx],
                    prev_data=self._days[idx - 1] if idx > 0 else None,
                    show_diff=True,
                ))

        def action_restore(self) -> None:
            idx = self._selected_idx()
            if 0 <= idx < len(self._days):
                self.app.push_screen(RestoreScreen(
                    repo=self._repo,
                    results_dir=self._results_dir,
                    preselect_day=self._days[idx]["day"],
                    day_data=self._days[idx],
                ))


    # ── Screen 5: endpointy + diff ────────────

    class EndpointDetailScreen(Screen):
        """Szczegóły endpointów dla wybranego dnia + opcjonalny diff."""

        BINDINGS = [
            Binding("escape", "pop_screen", "Wstecz"),
            Binding("r", "restore_selected", "Restore"),
        ]

        def __init__(
            self,
            day_data: dict,
            prev_data: Optional[dict],
            show_diff: bool = False,
        ) -> None:
            super().__init__()
            self._day = day_data
            self._prev = prev_data
            self._show_diff = show_diff

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            mode = "Diff vs poprzedni" if self._show_diff else "Endpointy"
            yield Label(f"{'🔍' if self._show_diff else '📋'} {mode} — {self._day['day']}", id="title")
            yield Label(f"Commit: {self._day['commit']}", classes="section-label")
            yield DataTable(id="ep-table", cursor_type="row")
            yield Horizontal(
                Button("◀ Wstecz", id="btn-back", variant="default"),
                Button("🔧 Restore wybrany", id="btn-restore", variant="warning"),
                id="action-row",
            )
            yield Footer()

        def on_mount(self) -> None:
            table = self.query_one("#ep-table", DataTable)

            if self._show_diff and self._prev:
                table.add_columns("Zmiana", "Method", "Path", "Status teraz", "Status poprzednio", "HTTP", "ms")
                changes = _endpoint_diff(self._prev["results"], self._day["results"])
                for c in changes:
                    change_label = {
                        "added": "[green]+added[/green]",
                        "removed": "[red]-removed[/red]",
                        "status_changed": "[yellow]~changed[/yellow]",
                    }.get(c["change"], c["change"])
                    table.add_row(
                        change_label,
                        c.get("method", ""),
                        c.get("path", ""),
                        c.get("status", ""),
                        c.get("prev_status", "—"),
                        str(c.get("http_status", "—")),
                        f"{c.get('response_time_ms', 0):.0f}" if c.get("response_time_ms") else "—",
                    )
                if not changes:
                    table.add_columns("Info")
                    table.add_row("[green]Brak zmian vs poprzedni dzień[/green]")
            else:
                table.add_columns("Method", "Path", "Status", "HTTP", "ms", "Error", "testql")
                for r in self._day["results"]:
                    status = r.get("status", "unknown")
                    status_colored = {
                        "ok": "[green]ok[/green]",
                        "fail": "[red]fail[/red]",
                        "timeout": "[yellow]timeout[/yellow]",
                        "skip": "[dim]skip[/dim]",
                    }.get(status, status)
                    tql = "[green]✓[/green]" if r.get("testql_passed") else (
                        "[red]✗[/red]" if r.get("testql_passed") is False else "—"
                    )
                    table.add_row(
                        r.get("method", "GET"),
                        r.get("path", ""),
                        status_colored,
                        str(r.get("http_status", "—")),
                        f"{r.get('response_time_ms', 0):.0f}" if r.get("response_time_ms") else "—",
                        (r.get("error") or "")[:40],
                        tql,
                    )

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "btn-back":
                self.app.pop_screen()
            elif event.button.id == "btn-restore":
                self.action_restore_selected()

        def action_restore_selected(self) -> None:
            table = self.query_one("#ep-table", DataTable)
            idx = table.cursor_row
            results = self._day["results"]
            if 0 <= idx < len(results):
                ep = results[idx]
                self.app.push_screen(RestoreScreen(
                    repo=Path("."),
                    results_dir=self._day["path"].parent,
                    preselect_day=self._day["day"],
                    preselect_endpoint=ep.get("path", ""),
                    day_data=self._day,
                ))


    # ── Screen 6: restore ────────────────────

    class RestoreScreen(Screen):
        """
        Restore endpoint jako izolowany projekt Docker z podanym URL/portem.
        """

        BINDINGS = [Binding("escape", "pop_screen", "Wstecz")]

        def __init__(
            self,
            repo: Path,
            results_dir: Path,
            preselect_day: str = "",
            preselect_endpoint: str = "",
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
                endpoints = [
                    r.get("path", "") for r in self._day_data.get("results", [])
                    if r.get("path")
                ]

            yield Label("Ścieżka endpointu:", classes="section-label")
            if endpoints:
                yield Select(
                    [(ep, ep) for ep in endpoints],
                    id="endpoint-select",
                    value=self._preselect_endpoint or endpoints[0],
                )
            else:
                yield Input(
                    value=self._preselect_endpoint or "/api/health",
                    id="endpoint-input",
                )

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
                sel = self.query_one("#endpoint-select", Select)
                return sel.value or "/api/health"
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
                "--output", output,
                "--results-dir", results_dir,
            ]
            log.write_line(f"$ {' '.join(cmd)}\n")

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                for line in proc.stdout:
                    log.write_line(line.rstrip())
                rc = proc.wait()
                status = self.query_one("#restore-status", Label)
                if rc == 0:
                    slug = endpoint.lstrip("/").replace("/", "-")
                    target = Path(output) / slug
                    status.update(
                        f"[green]✓ Przywrócono do {target}[/green]  "
                        f"Port Docker: {port}"
                    )
                    self._patch_docker_port(target, port)
                    self.query_one("#btn-docker", Button).disabled = False
                    self._last_target = target
                    self._last_port = port
                else:
                    status.update(f"[red]✗ Błąd (exit {rc})[/red]")
            except Exception as exc:
                log.write_line(f"[ERROR] {exc}")

        def _patch_docker_port(self, target: Path, port: str) -> None:
            """Aktualizuje port w docker-compose.yml przywróconego projektu."""
            dc = target / "docker" / "docker-compose.yml"
            if not dc.exists():
                return
            content = dc.read_text()
            import re
            content = re.sub(r'"?\d{4,5}:(\d{4,5})"?', f'"{port}:\\1"', content)
            dc.write_text(content)

        def _run_docker(self) -> None:
            target = getattr(self, "_last_target", None)
            port = getattr(self, "_last_port", "8099")
            if not target:
                return
            dc_dir = target / "docker"
            if not dc_dir.exists():
                dc_dir = target
            log = self.query_one("#restore-log", Log)
            cmd = ["docker", "compose", "up", "-d"]
            log.write_line(f"\n$ cd {dc_dir} && {' '.join(cmd)}\n")
            try:
                proc = subprocess.Popen(
                    cmd, cwd=dc_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                )
                for line in proc.stdout:
                    log.write_line(line.rstrip())
                rc = proc.wait()
                status = self.query_one("#restore-status", Label)
                if rc == 0:
                    endpoint = self._get_endpoint()
                    url = f"http://localhost:{port}{endpoint}"
                    status.update(f"[green]🐳 Uruchomiono!  URL: {url}[/green]")
                else:
                    status.update(f"[red]✗ docker compose up failed (exit {rc})[/red]")
            except FileNotFoundError:
                log.write_line("[ERROR] docker nie znaleziony — zainstaluj Docker Desktop")


    # ── Help Screen ───────────────────────────

    class HelpScreen(ModalScreen):
        BINDINGS = [Binding("escape", "dismiss", "Zamknij")]

        def compose(self) -> ComposeResult:
            yield Markdown("""
# rebuild TUI — Pomoc

## Skróty klawiszowe

| Klawisz | Akcja |
|---------|-------|
| `Ctrl+C` | Wyjdź |
| `Escape` | Wstecz |
| `D` | Diff vs poprzedni dzień |
| `R` | Restore wybranego endpointu |
| `Enter` | Szczegóły endpointów dnia |

## Przepływ

1. **Wybierz projekt** — podaj ścieżkę do repozytorium git
2. **Otwórz historię** — jeśli `.rebuild/` istnieje (po wcześniejszym walk)
3. **Nowy walk** — skonfiguruj i uruchom analizę historii
4. **Historia** — przeglądaj dzień po dniu, obserwuj health%
5. **Diff** — porównaj endpointy z poprzednim dniem
6. **Restore** — przywróć endpoint → izolowany projekt Docker

## testql vs deta

- **deta scan** — wykrywa ogólne usługi/porty z docker-compose
- **testql** — weryfikuje szczegółowe API endpoints przez scenariusze

""")
            yield Button("Zamknij", id="btn-close", variant="default")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            self.dismiss()


    # ── Główna aplikacja ──────────────────────

    REBUILD_CSS = """
Screen {
    background: $background;
}
#title {
    text-style: bold;
    color: $accent;
    padding: 1 2;
    height: 3;
}
.section-label {
    color: $text-muted;
    padding: 0 2;
    margin-top: 1;
}
.error {
    color: $error;
    padding: 0 2;
}
#action-row {
    height: 3;
    padding: 1 2;
    align: left middle;
}
#action-row Button {
    margin-right: 1;
}
#repo-row {
    height: 3;
    padding: 0 2;
}
#repo-row Input {
    width: 1fr;
}
#screenshots-row, #dryrun-row {
    height: 3;
    padding: 0 2;
    align: left middle;
}
#screenshots-row .section-label, #dryrun-row .section-label {
    width: 1fr;
    padding: 0;
    margin-top: 0;
}
DataTable {
    height: 1fr;
    margin: 0 2;
}
Log {
    height: 12;
    margin: 0 2;
    border: solid $accent;
}
#restore-status {
    padding: 0 2;
    height: 2;
}
#status-bar {
    padding: 0 2;
    color: $text-muted;
    height: 2;
}
"""

    class RebuildTUI(App):
        """Główna aplikacja TUI rebuild."""

        CSS = REBUILD_CSS
        TITLE = "rebuild"
        SUB_TITLE = "Historical Deployment Analysis"

        BINDINGS = [
            Binding("ctrl+c", "quit", "Quit", priority=True),
        ]

        def on_mount(self) -> None:
            self.push_screen(ProjectScreen())


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

def launch_tui() -> None:
    """Uruchamia TUI. Sprawdza dostępność Textual."""
    if not _TEXTUAL_OK:
        print("rebuild TUI wymaga Textual:\n  pip install 'textual>=0.60'")
        sys.exit(1)
    app = RebuildTUI()
    app.run()


if __name__ == "__main__":
    launch_tui()
