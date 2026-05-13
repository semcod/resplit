from __future__ import annotations
import ast
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from ..application.services.git_service import GitService


@dataclass
class FunctionQuality:
    func_name: str
    commit_sha: str
    complexity: int
    size_lines: int
    test_pass_rate: float
    score: float
    timestamp: datetime


class GitTruthAnalyzer:
    """
    Analyzes code evolution and identifies the 'best' versions of functions.
    Now correlates git history with actual test results from .rebuild directory.
    """

    def __init__(self, repo_path: Path, results_dir: Optional[Path] = None):
        self.repo_path = repo_path
        self.results_dir = results_dir or (repo_path / ".rebuild")
        self.git = GitService(repo_path)
        self._historical_results = self._load_historical_results()

    def analyze_function_history(self, file_path: Path, func_name: str) -> List[FunctionQuality]:
        qualities = []
        rel_path = file_path.relative_to(self.repo_path) if file_path.is_absolute() else file_path

        cmd = ["log", "--format=%H|%aI", "--", str(rel_path)]
        try:
            output = self.git._run_git(cmd)
        except Exception:
            return []

        for line in output.splitlines():
            if not line:
                continue
            sha, iso = line.split("|")
            ts = datetime.fromisoformat(iso)

            try:
                content = self.git._run_git(["show", f"{sha}:{rel_path}"])
                quality = self._analyze_content(content, func_name, sha, ts)
                if quality:
                    qualities.append(quality)
            except Exception:
                continue

        return sorted(qualities, key=lambda q: q.score, reverse=True)

    def _analyze_content(
        self, content: str, func_name: str, sha: str, ts: datetime
    ) -> Optional[FunctionQuality]:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return None

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                complexity = self._compute_complexity(node)
                size = node.end_lineno - node.lineno + 1 if hasattr(node, "end_lineno") else 0

                # Link with historical test results if available for this commit
                pass_rate = self._historical_results.get(sha, 1.0)  # Default to 1.0 if unknown

                # Advanced weighted scoring
                # Weights: PassRate (0.4), Complexity (0.3), Size (0.3)
                complexity_inv = 1 / (complexity + 1)
                size_inv = 1 / ((size / 10) + 1)

                score = (
                    (0.4 * pass_rate * 100) + (0.3 * complexity_inv * 100) + (0.3 * size_inv * 100)
                )

                return FunctionQuality(
                    func_name=func_name,
                    commit_sha=sha,
                    complexity=complexity,
                    size_lines=size,
                    test_pass_rate=pass_rate,
                    score=score,
                    timestamp=ts,
                )
        return None

    def _compute_complexity(self, node: ast.AST) -> int:
        score = 1
        for subnode in ast.walk(node):
            if isinstance(
                subnode, (ast.If, ast.While, ast.For, ast.And, ast.Or, ast.ExceptHandler, ast.With)
            ):
                score += 1
        return score

    def _load_historical_results(self) -> Dict[str, float]:
        """
        Loads all results from .rebuild directory and maps commit SHAs to health percentage.
        """
        history: Dict[str, float] = {}
        if not self.results_dir.exists():
            return history

        for day_dir in self.results_dir.iterdir():
            rf = day_dir / "results.json"
            cf = day_dir / "commit.txt"
            if rf.exists() and cf.exists():
                try:
                    # Get SHA from commit.txt
                    sha = cf.read_text().splitlines()[0]
                    # Get results
                    data = json.loads(rf.read_text())
                    if not data:
                        continue

                    ok_count = sum(1 for r in data if r.get("status") == "ok")
                    history[sha] = ok_count / len(data)
                except Exception:
                    continue
        return history
