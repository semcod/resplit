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

    def get_current_sha(self) -> str:
        return self._run_git(["rev-parse", "HEAD"]).strip()

    def clone_for_walk(self, output_dir: Path) -> "GitService":
        """
        Creates a local clone inside output_dir/repo/ for safe checkouts.
        The original repo is never modified.
        Returns a new GitService pointed at the clone.
        """
        clone_path = output_dir / "repo"
        if clone_path.exists():
            self.shell.run(["git", "fetch", "--quiet"], cwd=clone_path)
        else:
            clone_path.mkdir(parents=True, exist_ok=True)
            result = self.shell.run(
                ["git", "clone", "--local", "--no-hardlinks", str(self.repo_path), str(clone_path)]
            )
            if result.returncode != 0:
                raise RuntimeError(f"git clone failed: {result.stderr}")
        return GitService(clone_path, shell=self.shell)
    
    def sync_current_state(self, target_path: Path):
        """
        Copies all files (including untracked ones like node_modules)
        from current repo to target_path.
        Used for Accelerator Mode.
        """
        if not (target_path / ".git").exists():
            # Create a shared clone first to get the history/git objects
            # -s (shared) uses hardlinks for objects, which is extremely fast and saves space
            self.shell.run(["git", "clone", "-s", str(self.repo_path), str(target_path)])

        # Use rsync to overlay the current state (node_modules, untracked files)
        # We exclude .git during rsync to avoid messing up the target repo's git state
        self.shell.run([
            "rsync", "-av", "--exclude", ".rebuild", "--exclude", ".git",
            str(self.repo_path) + "/", str(target_path) + "/"
        ])

    def checkout(self, sha: str):
        self._run_git(["checkout", "--force", "--quiet", sha])

    def restore_head(self, sha: Optional[str] = None):
        target = sha or "HEAD"
        self._run_git(["checkout", "--force", "--quiet", target])

    def diff_names(self, from_sha: str, to_sha: str) -> Optional[List[str]]:
        """Return list of file paths changed between two commits, or None on error."""
        cmd = ["git", "diff", "--name-only", from_sha, to_sha]
        result = self.shell.run(cmd, cwd=self.repo_path)
        if result.returncode != 0:
            return None
        return [f for f in result.stdout.strip().splitlines() if f]

    def _run_git(self, args: List[str]) -> str:
        cmd = ["git"] + args
        result = self.shell.run(cmd, cwd=self.repo_path)
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr}")
        return result.stdout
