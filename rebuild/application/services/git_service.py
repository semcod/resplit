from __future__ import annotations
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple

from ...domain.commit import CommitInfo
from ...domain.models import WalkConfig
from .base import Service
from ...infrastructure.shell_adapter import ShellAdapter

class GitService(Service[WalkConfig, List[Tuple[date, CommitInfo]]]):
    """
    Service for interacting with Git repositories and history.
    Uses ShellAdapter for all git commands.
    """
    def __init__(self, repo_path: Path, shell: Optional[ShellAdapter] = None):
        self.repo_path = repo_path
        self.shell = shell or ShellAdapter()

    def execute(self, config: WalkConfig) -> List[Tuple[date, CommitInfo]]:
        return self.days_with_commits(config)

    def days_with_commits(self, config: WalkConfig) -> List[Tuple[date, CommitInfo]]:
        """Finds the earliest commit for each day in the given range."""
        results = []
        cmd = ["log", "--format=%H|%as|%s|%an|%aI", "--all", "-n", str(config.days * 10)]
        
        try:
            output = self._run_git(cmd)
        except Exception:
            return []

        seen_days = set()
        for line in output.splitlines():
            if not line: continue
            try:
                sha, day_str, msg, author, iso_ts = line.split("|", 4)
                day = date.fromisoformat(day_str)
                ts = datetime.fromisoformat(iso_ts)
                
                if config.date_from and day < config.date_from: continue
                if config.date_to and day > config.date_to: continue
                
                if day not in seen_days:
                    seen_days.add(day)
                    info = CommitInfo(
                        sha=sha,
                        message=msg,
                        author=author,
                        timestamp=ts,
                        date=day
                    )
                    results.append((day, info))
                    if len(results) >= config.days:
                        break
            except Exception:
                continue
        
        return sorted(results, key=lambda x: x[0])

    def checkout(self, sha: str):
        self._run_git(["checkout", sha, "--quiet"])

    def restore_head(self):
        self._run_git(["checkout", "-", "--quiet"])

    def _run_git(self, args: List[str]) -> str:
        cmd = ["git"] + args
        result = self.shell.run(cmd, cwd=self.repo_path)
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr}")
        return result.stdout
