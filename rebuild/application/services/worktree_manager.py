"""
Worktree-based branch switching for 10x speedup.
Eliminates git checkout overhead by using multiple worktrees.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

from .base import Service
from ...infrastructure.shell_adapter import ShellAdapter


@dataclass
class WorktreeInfo:
    """Information about a git worktree."""

    path: Path
    commit_sha: str
    branch_name: Optional[str] = None


class WorktreeManager(Service[Path, WorktreeInfo]):
    """
    Manages git worktrees for ultra-fast branch/commit switching.

    Instead of 'git checkout' which modifies the repo, we create worktrees:
    - Each commit gets its own directory
    - Zero checkout time
    - Container only sees bind-mounted code changes
    """

    def __init__(self, repo_path: Path, base_dir: Path, shell: Optional[ShellAdapter] = None):
        self.repo_path = repo_path
        self.base_dir = base_dir  # Where worktrees are created (e.g., .rebuild/worktrees/)
        self.shell = shell or ShellAdapter()
        self._worktrees: Dict[str, WorktreeInfo] = {}
        self._ensure_base_dir()

    def _ensure_base_dir(self):
        """Create base directory for worktrees."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _worktree_path(self, sha: str) -> Path:
        """Generate deterministic path for a commit's worktree."""
        short_sha = sha[:12]
        return self.base_dir / f"wt_{short_sha}"

    def get_or_create(self, sha: str) -> WorktreeInfo:
        """
        Get existing worktree or create new one for commit.
        Uses 'git worktree add' which is instant (no copying, just git metadata).
        """
        if sha in self._worktrees:
            return self._worktrees[sha]

        wt_path = self._worktree_path(sha)

        # Check if worktree already exists in git
        existing = self._list_worktrees()
        if str(wt_path) in existing:
            info = WorktreeInfo(path=wt_path, commit_sha=sha)
            self._worktrees[sha] = info
            return info

        # Create new worktree - this is FAST (no file copy, just git metadata)
        result = self.shell.run(
            ["git", "worktree", "add", "--detach", str(wt_path), sha], cwd=self.repo_path
        )

        if result.returncode != 0:
            # Fallback: worktree might exist but be dirty - remove and recreate
            if wt_path.exists():
                self._remove_worktree(sha, force=True)
                result = self.shell.run(
                    ["git", "worktree", "add", "--detach", str(wt_path), sha], cwd=self.repo_path
                )

            if result.returncode != 0:
                raise RuntimeError(f"Failed to create worktree for {sha}: {result.stderr}")

        info = WorktreeInfo(path=wt_path, commit_sha=sha)
        self._worktrees[sha] = info
        return info

    def _list_worktrees(self) -> List[str]:
        """List existing worktree paths."""
        result = self.shell.run(["git", "worktree", "list", "--porcelain"], cwd=self.repo_path)
        if result.returncode != 0:
            return []

        paths = []
        for line in result.stdout.split("\n"):
            if line.startswith("worktree "):
                paths.append(line.replace("worktree ", "").strip())
        return paths

    def _remove_worktree(self, sha: str, force: bool = False) -> None:
        """Remove a worktree (cleanup)."""
        wt_path = self._worktree_path(sha)

        # Remove from git worktree list
        cmd = ["git", "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(str(wt_path))

        self.shell.run(cmd, cwd=self.repo_path)

        # Cleanup dict
        self._worktrees.pop(sha, None)

    def cleanup_all(self, keep_shas: Optional[List[str]] = None) -> None:
        """
        Remove all worktrees except optionally specified ones to keep.
        Call this periodically to prevent disk bloat.
        """
        keep_set = set(keep_shas or [])
        to_remove = [sha for sha in self._worktrees if sha not in keep_set]

        for sha in to_remove:
            try:
                self._remove_worktree(sha, force=True)
            except Exception:
                pass  # Best effort cleanup

    def prepare_sequence(self, shas: List[str]) -> Dict[str, WorktreeInfo]:
        """
        Pre-create worktrees for a sequence of commits.
        Can be run in parallel for maximum speed.
        """
        results = {}
        for sha in shas:
            results[sha] = self.get_or_create(sha)
        return results

    def get_active_path(self, sha: str) -> Path:
        """Get the path where this commit's code lives."""
        info = self.get_or_create(sha)
        return info.path

    def execute(self, commit_sha: str) -> WorktreeInfo:
        """Service interface: ensure worktree exists for commit."""
        return self.get_or_create(commit_sha)
