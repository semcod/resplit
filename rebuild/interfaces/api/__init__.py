"""FastAPI-based REST + WebSocket interface for rebuild."""

from .app import create_app

__all__ = ["create_app"]
