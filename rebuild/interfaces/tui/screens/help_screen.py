from __future__ import annotations

from ..compat import TEXTUAL_OK

if TEXTUAL_OK:
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.screen import ModalScreen
    from textual.widgets import Button, Markdown

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
| `Enter` | Szczegóły endpointów dnia |
| `D` | Diff vs poprzedni dzień |
| `R` | Restore wybranego endpointu |
| `J` / `K` | W dół / W górę (nawigacja w tabeli) |
| `G` | Początek tabeli |
| `Shift+G` | Koniec tabeli |
| `F` | Filtruj endpointy (TODO) |

## Przepływ

1. **Wybierz projekt** — podaj ścieżkę do repozytorium git
2. **Otwórz historię** — jeśli `.rebuild/` istnieje (po wcześniejszym walk)
3. **Nowy walk** — skonfiguruj i uruchom analizę historii
4. **Historia** — przeglądaj dzień po dniu, obserwuj health%
5. **Diff** — porównaj endpointy z poprzednim dniem
6. **Restore** — przywróć endpoint → izolowany projekt Docker
""")
            yield Button("Zamknij", id="btn-close", variant="default")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            self.dismiss()
else:
    class HelpScreen:
        """Fallback export used when Textual is not installed."""

        BINDINGS = []
