"""
rebuild.tui_data_service — domain logic extracted from TUI for reusability.

Provides data loading, calculation, and diff operations for the TUI interface.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Optional


class TUIDataService:
    """Service for TUI data operations - loads results, calculates metrics, computes diffs."""

    @staticmethod
    def load_day_results(results_dir: Path) -> List[Dict]:
        """Load results from all .rebuild/YYYY-MM-DD/ subdirectories."""
        days = []
        for d in sorted(results_dir.iterdir()):
            rf = d / "results.json"
            if not d.is_dir() or not rf.exists():
                continue
            try:
                from datetime import date

                date.fromisoformat(d.name)
            except ValueError:
                continue
            try:
                results = json.loads(rf.read_text())
            except (json.JSONDecodeError, OSError):
                results = []
            commit_txt = (
                (d / "commit.txt").read_text().strip() if (d / "commit.txt").exists() else ""
            )
            days.append(
                {
                    "day": d.name,
                    "results": results,
                    "commit": commit_txt.split("\n")[0][:50] if commit_txt else "—",
                    "path": d,
                }
            )
        return days

    @staticmethod
    def endpoint_diff(prev: List[Dict], curr: List[Dict]) -> List[Dict]:
        """
        Compare two lists of endpoint results (from results.json).
        Returns list of changes: added / removed / status_changed.
        """
        prev_map = {(r["method"], r["path"]): r for r in prev}
        curr_map = {(r["method"], r["path"]): r for r in curr}

        changes = []
        for key, r in curr_map.items():
            if key not in prev_map:
                changes.append({**r, "change": "added"})
            elif prev_map[key]["status"] != r["status"]:
                changes.append(
                    {
                        **r,
                        "change": "status_changed",
                        "prev_status": prev_map[key]["status"],
                    }
                )
        for key, r in prev_map.items():
            if key not in curr_map:
                changes.append({**r, "change": "removed"})

        return changes

    @staticmethod
    def health_bar(pct: float, width: int = 20) -> str:
        """Generate a visual health bar string."""
        filled = int(pct / 100 * width)
        bar = "█" * filled + "░" * (width - filled)
        color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
        return f"[{color}]{bar}[/{color}] {pct:.0f}%"

    @staticmethod
    def calc_health(results: List[Dict]) -> float:
        """Calculate health percentage from endpoint results."""
        if not results:
            return 0.0
        ok = sum(1 for r in results if r.get("status") == "ok")
        return round(ok / len(results) * 100, 1)

    @staticmethod
    def get_git_repo_toplevel(cwd: Path = Path(".")) -> Optional[str]:
        """Get the git repository toplevel path."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
