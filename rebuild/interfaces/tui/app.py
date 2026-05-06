from __future__ import annotations

import sys

from .compat import TEXTUAL_OK

_REBUILD_CSS = """
Screen { background: $background; }
#title { text-style: bold; color: $accent; padding: 1 2; height: 3; }
.section-label { color: $text-muted; padding: 0 2; margin-top: 1; }
.error { color: $error; padding: 0 2; }
#action-row { height: 3; padding: 1 2; align: left middle; }
#action-row Button { margin-right: 1; }
#repo-row { height: 3; padding: 0 2; }
#repo-row Input { width: 1fr; }
#screenshots-row, #dryrun-row { height: 3; padding: 0 2; align: left middle; }
#screenshots-row .section-label, #dryrun-row .section-label { width: 1fr; padding: 0; margin-top: 0; }
DataTable { height: 1fr; margin: 0 2; }
Log { height: 12; margin: 0 2; border: solid $accent; }
#restore-status { padding: 0 2; height: 2; }
#status-bar { padding: 0 2; color: $text-muted; height: 2; }
"""

if TEXTUAL_OK:
    from textual.app import App
    from textual.binding import Binding

    class RebuildTUI(App):
        """Główna aplikacja TUI rebuild."""

        CSS = _REBUILD_CSS
        TITLE = "rebuild"
        SUB_TITLE = "Historical Deployment Analysis"
        BINDINGS = [Binding("ctrl+c", "quit", "Quit", priority=True)]

        def on_mount(self) -> None:
            from .screens.project_screen import ProjectScreen
            self.push_screen(ProjectScreen())
else:
    class RebuildTUI:
        """Fallback export used when Textual is not installed."""

        TITLE = "rebuild"
        SUB_TITLE = "Historical Deployment Analysis"
        BINDINGS = []

        def run(self) -> None:
            raise RuntimeError("rebuild TUI requires textual>=0.60")


def launch_tui() -> None:
    """Uruchamia TUI. Sprawdza dostępność Textual."""
    if not TEXTUAL_OK:
        print("rebuild TUI wymaga Textual:\n  pip install 'textual>=0.60'")
        sys.exit(1)
    RebuildTUI().run()
