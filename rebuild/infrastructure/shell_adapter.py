from __future__ import annotations
import subprocess
from pathlib import Path
from typing import List, Optional
from rich.console import Console

class ShellAdapter:
    """
    Adapter for shell command execution.
    Centralizes logging, error handling, and subprocess management.
    """
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def run(self, cmd: List[str], cwd: Optional[Path] = None, capture: bool = True) -> subprocess.CompletedProcess:
        try:
            if not capture:
                return subprocess.run(cmd, cwd=cwd, check=False)

            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False
            )
            return result
        except Exception as e:
            self.console.print(f"[red]Shell error executing {' '.join(cmd)}: {e}[/red]")
            raise

    def popen(self, cmd: List[str], cwd: Optional[Path] = None) -> subprocess.Popen:
        return subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
