from __future__ import annotations

from pathlib import Path

from ....application.services.tui_data_service import TUIDataService
from ..compat import TEXTUAL_OK

if TEXTUAL_OK:
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal
    from textual.screen import Screen
    from textual.widgets import Button, DataTable, Footer, Header, Label, Static

    class HistoryScreen(Screen):
        """Tabela: dzień | commit | endpointy | health% | diff vs poprzedni dzień."""

        BINDINGS = [
            Binding("escape", "pop_screen", "Wstecz"),
            Binding("d", "show_diff", "Diff"),
            Binding("r", "restore", "Restore"),
            Binding("enter", "show_endpoints", "Endpointy"),
            Binding("j", "cursor_down", "W dół"),
            Binding("k", "cursor_up", "W górę"),
            Binding("g", "go_top", "Początek"),
            Binding("G", "go_bottom", "Koniec"),
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
            self._days = TUIDataService.load_day_results(self._results_dir)
            table = self.query_one("#history-table", DataTable)
            table.add_columns("Dzień", "Commit", "#EP", "OK", "FAIL", "Health%", "Δ vs poprzedni")

            for i, d in enumerate(self._days):
                results = d["results"]
                health = TUIDataService.calc_health(results)
                ok = sum(1 for r in results if r.get("status") == "ok")
                fail = sum(1 for r in results if r.get("status") not in ("ok", "skip", "skip_method", "skip_auth"))
                total = len(results)

                if i > 0:
                    prev = self._days[i - 1]["results"]
                    changes = TUIDataService.endpoint_diff(prev, results)
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
                    d["day"], d["commit"], str(total),
                    f"[green]{ok}[/green]", f"[red]{fail}[/red]",
                    health_str, delta,
                )

            self.query_one("#status-bar", Static).update(
                f"{len(self._days)} dni  ·  [dim]D=diff  R=restore  Enter=endpointy[/dim]"
            )

        def _selected_idx(self) -> int:
            return self.query_one("#history-table", DataTable).cursor_row

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "btn-back":
                self.app.pop_screen()
            elif event.button.id in ("btn-diff", "btn-endpoints"):
                idx = self._selected_idx()
                if 0 <= idx < len(self._days):
                    from .endpoint_screens import EndpointDetailScreen
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
                from .endpoint_screens import EndpointDetailScreen
                self.app.push_screen(EndpointDetailScreen(
                    day_data=self._days[idx],
                    prev_data=self._days[idx - 1] if idx > 0 else None,
                    show_diff=False,
                ))

        def action_show_diff(self) -> None:
            idx = self._selected_idx()
            if 0 <= idx < len(self._days):
                from .endpoint_screens import EndpointDetailScreen
                self.app.push_screen(EndpointDetailScreen(
                    day_data=self._days[idx],
                    prev_data=self._days[idx - 1] if idx > 0 else None,
                    show_diff=True,
                ))

        def action_show_endpoints(self) -> None:
            idx = self._selected_idx()
            if 0 <= idx < len(self._days):
                from .endpoint_screens import EndpointDetailScreen
                self.app.push_screen(EndpointDetailScreen(
                    day_data=self._days[idx],
                    prev_data=self._days[idx - 1] if idx > 0 else None,
                    show_diff=False,
                ))

        def action_cursor_down(self) -> None:
            table = self.query_one("#history-table", DataTable)
            if table.cursor_row < len(self._days) - 1:
                table.cursor_row += 1

        def action_cursor_up(self) -> None:
            table = self.query_one("#history-table", DataTable)
            if table.cursor_row > 0:
                table.cursor_row -= 1

        def action_go_top(self) -> None:
            table = self.query_one("#history-table", DataTable)
            table.cursor_row = 0

        def action_go_bottom(self) -> None:
            table = self.query_one("#history-table", DataTable)
            table.cursor_row = len(self._days) - 1

        def action_restore(self) -> None:
            idx = self._selected_idx()
            if 0 <= idx < len(self._days):
                from .restore_screen import RestoreScreen
                self.app.push_screen(RestoreScreen(
                    repo=self._repo, results_dir=self._results_dir,
                    preselect_day=self._days[idx]["day"], day_data=self._days[idx],
                ))
else:
    class HistoryScreen:
        """Fallback export used when Textual is not installed."""

        BINDINGS = []

        def __init__(self, repo: Path, results_dir: Path) -> None:
            self._repo = repo
            self._results_dir = results_dir
