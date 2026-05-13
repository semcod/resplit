"""Graceful Textual import guard."""

from __future__ import annotations

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

    TEXTUAL_OK = True
except ImportError:
    TEXTUAL_OK = False
    App = object
    ComposeResult = object
    Binding = object
    Screen = object
    ModalScreen = object
    Button = DataTable = Footer = Header = Input = Label = object
    ListItem = ListView = Log = Markdown = ProgressBar = object
    Select = Static = Switch = object
    Horizontal = Vertical = Container = ScrollableContainer = object
