from __future__ import annotations

from pathlib import Path

from ....application.services.tui_data_service import TUIDataService
from ..compat import TEXTUAL_OK

if TEXTUAL_OK:
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal
    from textual.screen import Screen
    from textual.widgets import Button, Footer, Header, Input, Label

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
                Input(placeholder="/path/to/repo  lub  . dla bieżącego", id="repo-input"),
                Button("Browse recent", id="btn-browse", variant="default"),
                id="repo-row",
            )
            yield Label("Katalog wyników (.rebuild/):", classes="section-label")
            yield Input(placeholder=".rebuild  (domyślnie)", id="results-input")
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
            return Path(val).expanduser() if val else self._repo_path() / ".rebuild"

        def _populate_recent(self) -> None:
            toplevel = TUIDataService.get_git_repo_toplevel(Path("."))
            if toplevel:
                self.query_one("#repo-input", Input).value = toplevel

        def _open_history(self) -> None:
            from .history_screen import HistoryScreen
            repo = self._repo_path()
            results_dir = self._results_dir()
            err = self.query_one("#repo-error", Label)
            if not results_dir.exists():
                err.update(f"⚠ Brak katalogu wyników: {results_dir}")
                return
            err.update("")
            self.app.push_screen(HistoryScreen(repo=repo, results_dir=results_dir))

        def _new_walk(self) -> None:
            from .walk_screens import WalkConfigScreen
            repo = self._repo_path()
            err = self.query_one("#repo-error", Label)
            if not (repo / ".git").exists():
                err.update(f"⚠ Nie znaleziono repozytorium git: {repo}")
                return
            err.update("")
            self.app.push_screen(WalkConfigScreen(repo=repo))

        def action_help(self) -> None:
            from .help_screen import HelpScreen
            self.app.push_screen(HelpScreen())
else:
    class ProjectScreen:
        """Fallback export used when Textual is not installed."""

        BINDINGS = []
