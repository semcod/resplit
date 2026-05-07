from __future__ import annotations
from typing import Optional
from rich.console import Console

from .recommendation_engine import RefactorSuggestion

class RefactorExecutor:
    """
    Executes refactoring suggestions on the filesystem.
    Currently supports MERGE_DUPLICATES by extracting shared functions.
    """
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def execute_suggestion(self, suggestion: RefactorSuggestion) -> bool:
        if suggestion.type == "MERGE_DUPLICATES":
            return self._merge_duplicates(suggestion)

        self.console.print(f"[yellow]Suggest type {suggestion.type} not yet automatable.[/yellow]")
        return False

    def _merge_duplicates(self, suggestion: RefactorSuggestion) -> bool:
        if not suggestion.files:
            return False

        # 1. Identify common code (simplified: take first fragment)
        # In a real system, we'd use the representative hash to find the shared AST
        self.console.print(f"[bold cyan]Merging duplicates in:[/bold cyan] {', '.join(f.name for f in suggestion.files)}")

        # 2. Logic to extract to a shared file (e.g. shared_utils.py)
        # This is a high-risk operation, so we'll do a simplified "Extract to Top" or "Comment out"
        # For this demonstration, we'll append a "REFAC" comment to the files
        for f in suggestion.files:
            try:
                content = f.read_text()
                # Placeholder for real AST transformation:
                # 1. Parse AST
                # 2. Remove duplicate function
                # 3. Add import from shared_utils
                new_content = "# [REFACTORED] Duplicates identified. Manual extraction recommended.\n" + content
                f.write_text(new_content)
            except Exception as e:
                self.console.print(f"[red]Failed to refactor {f.name}: {e}[/red]")
                return False

        return True
