from __future__ import annotations

from pathlib import Path
from typing import Optional

from ....application.services.tui_data_service import TUIDataService
from ..compat import TEXTUAL_OK

if TEXTUAL_OK:
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal
    from textual.screen import Screen
    from textual.widgets import Button, DataTable, Footer, Header, Label

    _STATUS_COLORS = {
        "ok": "[green]ok[/green]",
        "fail": "[red]fail[/red]",
        "fail_auth": "[red]fail_auth[/red]",
        "fail_server": "[red]fail_server[/red]",
        "fail_network": "[yellow]fail_network[/yellow]",
        "fail_template": "[yellow]fail_template[/yellow]",
        "timeout": "[yellow]timeout[/yellow]",
        "skip": "[dim]skip[/dim]",
        "skip_method": "[dim]skip_method[/dim]",
        "skip_auth": "[dim]skip_auth[/dim]",
    }

    class EndpointDetailScreen(Screen):
        """Szczegóły endpointów dla wybranego dnia + opcjonalny diff."""

        BINDINGS = [
            Binding("escape", "pop_screen", "Wstecz"),
            Binding("r", "restore_selected", "Restore"),
            Binding("j", "cursor_down", "W dół"),
            Binding("k", "cursor_up", "W górę"),
            Binding("g", "go_top", "Początek"),
            Binding("G", "go_bottom", "Koniec"),
            Binding("f", "filter", "Filtruj"),
        ]

        def __init__(self, day_data: dict, prev_data: Optional[dict], show_diff: bool = False) -> None:
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
                changes = TUIDataService.endpoint_diff(self._prev["results"], self._day["results"])
                for c in changes:
                    change_label = {
                        "added": "[green]+added[/green]",
                        "removed": "[red]-removed[/red]",
                        "status_changed": "[yellow]~changed[/yellow]",
                    }.get(c["change"], c["change"])
                    table.add_row(
                        change_label, c.get("method", ""), c.get("path", ""),
                        c.get("status", ""), c.get("prev_status", "—"),
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
                    status_colored = _STATUS_COLORS.get(status, status)
                    tql = "[green]✓[/green]" if r.get("testql_passed") else (
                        "[red]✗[/red]" if r.get("testql_passed") is False else "—"
                    )
                    table.add_row(
                        r.get("method", "GET"), r.get("path", ""),
                        status_colored, str(r.get("http_status", "—")),
                        f"{r.get('response_time_ms', 0):.0f}" if r.get("response_time_ms") else "—",
                        (r.get("error") or r.get("fail_reason") or "")[:40], tql,
                    )

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "btn-back":
                self.app.pop_screen()
            elif event.button.id == "btn-restore":
                self.action_restore_selected()

        def action_restore_selected(self) -> None:
            from .restore_screen import RestoreScreen
            table = self.query_one("#ep-table", DataTable)
            idx = table.cursor_row
            results = self._day["results"]
            if 0 <= idx < len(results):
                ep = results[idx]
                self.app.push_screen(RestoreScreen(
                    repo=Path("."),
                    results_dir=Path(self._day.get("path", ".")).parent,
                    preselect_day=self._day["day"],
                    preselect_endpoint=ep.get("path", ""),
                    day_data=self._day,
                ))

        def action_cursor_down(self) -> None:
            table = self.query_one("#ep-table", DataTable)
            row_count = table.row_count
            if table.cursor_row < row_count - 1:
                table.cursor_row += 1

        def action_cursor_up(self) -> None:
            table = self.query_one("#ep-table", DataTable)
            if table.cursor_row > 0:
                table.cursor_row -= 1

        def action_go_top(self) -> None:
            table = self.query_one("#ep-table", DataTable)
            table.cursor_row = 0

        def action_go_bottom(self) -> None:
            table = self.query_one("#ep-table", DataTable)
            table.cursor_row = table.row_count - 1

        def action_filter(self) -> None:
            # TODO: Implement filter dialog for endpoints
            pass
