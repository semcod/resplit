"""
Git-diff driven test selection.
Only test endpoints affected by code changes.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass

from .base import Service
from ...domain.endpoint import Endpoint
from ...infrastructure.shell_adapter import ShellAdapter


@dataclass
class ChangedModule:
    """Information about a changed module/file."""
    path: Path
    change_type: str  # A=added, M=modified, D=deleted, R=renamed
    old_path: Optional[Path] = None


@dataclass
class TestSelection:
    """Result of test selection process."""
    endpoints_to_test: List[Endpoint]
    skipped_endpoints: List[Tuple[Endpoint, str]]  # (endpoint, reason)
    changed_modules: List[ChangedModule]
    confidence: str  # 'high', 'medium', 'low'


class SmartTestSelector(Service[Tuple[str, str], TestSelection]):
    """
    Selectively runs tests based on git diff analysis.
    
    Instead of testing all endpoints for every commit:
    1. Analyze which files changed
    2. Map file paths to affected endpoints
    3. Only test impacted endpoints + critical paths
    
    This gives massive speedup for large APIs where only small
    parts change between commits.
    """
    
    def __init__(self, repo_path: Path, shell: Optional[ShellAdapter] = None):
        self.repo_path = repo_path
        self.shell = shell or ShellAdapter()
        
        # Path patterns that affect specific endpoints
        self._path_patterns: Dict[str, List[str]] = {
            # FastAPI/Flask/Django patterns
            r"routers/auth\.py": ["/api/auth", "/api/login", "/api/logout"],
            r"routers/users?\.py": ["/api/users", "/api/user"],
            r"routers/orders?\.py": ["/api/orders", "/api/order"],
            r"models/user": ["/api/users", "/api/auth"],
            r"models/order": ["/api/orders"],
            r"migrations/": ["/api/*"],  # DB changes affect everything
            r"core/config": ["/api/*"],  # Config changes affect everything
            r"main\.py": ["/api/*"],  # Entry point changes affect everything
        }
        
        # Always-test endpoints (critical paths)
        self._critical_endpoints: Set[str] = {
            "/health", "/api/health", "/metrics"
        }
    
    def analyze_changes(self, commit_from: str, commit_to: str) -> List[ChangedModule]:
        """
        Get list of changed files between two commits.
        """
        result = self.shell.run(
            ["git", "diff", "--name-status", f"{commit_from}..{commit_to}"],
            cwd=self.repo_path
        )
        
        if result.returncode != 0:
            return []
        
        changes = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            
            parts = line.split("\t")
            if not parts:
                continue
            
            change_type = parts[0][0]  # First char: A, M, D, R
            
            if change_type == "R" and len(parts) >= 3:
                # Rename: R100	old	new
                old_path = Path(parts[1])
                new_path = Path(parts[2])
                changes.append(ChangedModule(new_path, change_type, old_path))
            elif len(parts) >= 2:
                path = Path(parts[1])
                changes.append(ChangedModule(path, change_type))
        
        return changes
    
    def select_tests(
        self,
        all_endpoints: List[Endpoint],
        changed_modules: List[ChangedModule],
        previous_commit: Optional[str] = None
    ) -> TestSelection:
        """
        Select which endpoints to test based on changed files.
        """
        if not changed_modules:
            # No changes detected - run critical only
            critical = [ep for ep in all_endpoints if ep.path in self._critical_endpoints]
            skipped = [(ep, "No relevant changes") for ep in all_endpoints if ep not in critical]
            return TestSelection(
                endpoints_to_test=critical,
                skipped_endpoints=skipped,
                changed_modules=[],
                confidence="high"
            )
        
        # Find affected endpoint patterns
        affected_patterns: Set[str] = set()
        
        for module in changed_modules:
            path_str = str(module.path)
            
            # Check against all patterns
            for pattern, endpoints in self._path_patterns.items():
                if re.search(pattern, path_str):
                    affected_patterns.update(endpoints)
        
        # If migrations or core files changed, test everything
        test_all = any(
            str(m.path).startswith(("migrations/", "core/", "config"))
            for m in changed_modules
        )
        
        if test_all:
            return TestSelection(
                endpoints_to_test=all_endpoints,
                skipped_endpoints=[],
                changed_modules=changed_modules,
                confidence="low"  # Low confidence = test everything
            )
        
        # Select endpoints to test
        to_test: List[Endpoint] = []
        skipped: List[Tuple[Endpoint, str]] = []
        
        for ep in all_endpoints:
            # Always test critical endpoints
            if ep.path in self._critical_endpoints:
                to_test.append(ep)
                continue
            
            # Test if matches affected pattern
            should_test = any(
                self._path_matches(ep.path, pattern)
                for pattern in affected_patterns
            )
            
            if should_test:
                to_test.append(ep)
            else:
                skipped.append((ep, "No affected code paths"))
        
        confidence = "high" if affected_patterns else "medium"
        
        return TestSelection(
            endpoints_to_test=to_test,
            skipped_endpoints=skipped,
            changed_modules=changed_modules,
            confidence=confidence
        )
    
    def _path_matches(self, endpoint_path: str, pattern: str) -> bool:
        """Check if endpoint matches a path pattern."""
        # Convert glob-style pattern to check
        pattern = pattern.rstrip("*")
        return endpoint_path.startswith(pattern)
    
    def add_mapping(self, file_pattern: str, affected_endpoints: List[str]):
        """Add custom file-to-endpoint mapping."""
        self._path_patterns[file_pattern] = affected_endpoints
    
    def execute(self, commit_range: Tuple[str, str]) -> TestSelection:
        """
        Service interface: analyze diff and select tests.
        """
        commit_from, commit_to = commit_range
        changes = self.analyze_changes(commit_from, commit_to)
        
        # Get all endpoints from scanner (would be passed in real usage)
        # For service interface, we return just the change analysis
        # The actual endpoint selection happens with select_tests()
        
        return TestSelection(
            endpoints_to_test=[],
            skipped_endpoints=[],
            changed_modules=changes,
            confidence="high"
        )
    
    def get_changed_modules(self, commit_from: str, commit_to: str) -> List[ChangedModule]:
        """Public method to get changed modules."""
        return self.analyze_changes(commit_from, commit_to)
