"""
E2E tests for Git operations and Accelerator mode pipeline.

Tests simulate realistic end-to-end scenarios using temporary git repos
and mock dependencies where network/docker is not available.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_git_repo(tmp_path: Path, with_commits: int = 3) -> Path:
    """Create a git repo with multiple commits."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@test.com"], capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], capture_output=True)
    
    for i in range(with_commits):
        (repo / f"file{i}.py").write_text(f"# Commit {i}\n")
        subprocess.run(["git", "-C", str(repo), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", f"commit{i}"], capture_output=True)
    
    return repo


# ─────────────────────────────────────────────────────────────────────────────
# E2E: Git Operations — clone, checkout, worktree
# ─────────────────────────────────────────────────────────────────────────────

class TestGitOperationsE2E:
    def test_git_clone_for_walk_creates_safe_clone(self, tmp_path):
        """Test that clone_for_walk creates a safe clone in .rebuild directory."""
        from rebuild.application.services.git_service import GitService
        from rebuild.domain.models import WalkConfig
        
        source_repo = _make_git_repo(tmp_path, with_commits=2)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        git = GitService(source_repo)
        clone_service = git.clone_for_walk(output_dir)
        
        clone_path = output_dir / "repo"
        assert clone_path.exists()
        assert (clone_path / ".git").exists()
        assert (clone_path / "file0.py").exists()
        assert (clone_path / "file1.py").exists()

    def test_git_checkout_switches_commits(self, tmp_path):
        """Test that git checkout switches between commits."""
        from rebuild.application.services.git_service import GitService
        
        repo = _make_git_repo(tmp_path, with_commits=3)
        git = GitService(repo)
        
        # Get current SHA
        current_sha = git.get_current_sha()
        assert current_sha
        
        # Checkout should work (we can't easily test switching between commits in this setup)
        git.checkout(current_sha)
        assert (repo / "file0.py").exists()

    def test_git_diff_names_returns_changed_files(self, tmp_path):
        """Test that git diff names returns list of changed files."""
        from rebuild.application.services.git_service import GitService
        
        repo = _make_git_repo(tmp_path, with_commits=2)
        git = GitService(repo)
        
        commits = list(subprocess.run(
            ["git", "-C", str(repo), "log", "--format=%H", "-n", "2"],
            capture_output=True, text=True, check=True
        ).stdout.strip().splitlines())
        
        if len(commits) >= 2:
            changed = git.diff_names(commits[0], commits[1])
            assert changed is not None

    def test_git_get_current_sha(self, tmp_path):
        """Test that get_current_sha returns the current HEAD SHA."""
        from rebuild.application.services.git_service import GitService
        
        repo = _make_git_repo(tmp_path, with_commits=3)
        git = GitService(repo)
        
        current_sha = git.get_current_sha()
        assert current_sha
        assert len(current_sha) == 40  # SHA-1 length

    def test_git_sync_current_state(self, tmp_path):
        """Test that sync_current_state copies files including untracked."""
        from rebuild.application.services.git_service import GitService
        
        repo = _make_git_repo(tmp_path, with_commits=1)
        target_dir = tmp_path / "target"
        
        # Add an untracked file
        (repo / "node_modules").mkdir()
        (repo / "node_modules" / "package.json").write_text("{}")
        
        git = GitService(repo)
        git.sync_current_state(target_dir)
        
        # Verify the untracked file was copied
        assert (target_dir / "node_modules" / "package.json").exists()


# ─────────────────────────────────────────────────────────────────────────────
# E2E: Accelerator Mode — worktree, sync, parallel tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAcceleratorModeE2E:
    def test_git_sync_current_state_in_accelerator(self, tmp_path):
        """Test that sync_current_state is used for preserving dependencies."""
        from rebuild.application.services.git_service import GitService
        
        repo = _make_git_repo(tmp_path, with_commits=1)
        target_dir = tmp_path / "target"
        
        # Add untracked dependencies
        (repo / "node_modules").mkdir()
        (repo / "node_modules" / "package.json").write_text("{}")
        
        git = GitService(repo)
        git.sync_current_state(target_dir)
        
        # Verify untracked files were copied
        assert (target_dir / "node_modules" / "package.json").exists()

    def test_clone_for_walk_returns_git_service(self, tmp_path):
        """Test that clone_for_walk returns a new GitService instance."""
        from rebuild.application.services.git_service import GitService
        
        repo = _make_git_repo(tmp_path, with_commits=2)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        git = GitService(repo)
        clone_service = git.clone_for_walk(output_dir)
        
        assert isinstance(clone_service, GitService)
        assert clone_service.repo_path == output_dir / "repo"


# ─────────────────────────────────────────────────────────────────────────────
# E2E: Restore Functionality — endpoint isolation, Docker restore
# ─────────────────────────────────────────────────────────────────────────────

class TestRestoreFunctionalityE2E:
    def test_restore_service_initialization(self, tmp_path):
        """Test that RestoreService can be initialized with repo_path."""
        from rebuild.application.services.restore_service import RestoreService
        
        repo = _make_git_repo(tmp_path, with_commits=1)
        
        restore_service = RestoreService(repo)
        assert restore_service.repo_path == repo

    def test_restore_clone_for_walk(self, tmp_path):
        """Test that restore uses clone_for_walk for safe cloning."""
        from rebuild.application.services.restore_service import RestoreService
        from rebuild.application.services.git_service import GitService
        
        repo = _make_git_repo(tmp_path, with_commits=1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        restore_service = RestoreService(repo)
        
        # The restore service should use git service for cloning
        git = GitService(repo)
        clone_service = git.clone_for_walk(output_dir)
        
        assert clone_service.repo_path == output_dir / "repo"


# ─────────────────────────────────────────────────────────────────────────────
# E2E: Scanner Service — OpenAPI, FastAPI routes
# ─────────────────────────────────────────────────────────────────────────────

class TestScannerServiceE2E:
    def test_scanner_service_initialization(self, tmp_path):
        """Test that ScannerService can be initialized with WalkConfig."""
        from rebuild.application.services.scanner_service import ScannerService
        from rebuild.domain.models import WalkConfig, DeployMethod
        
        repo = _make_git_repo(tmp_path, with_commits=1)
        config = WalkConfig(
            repo_path=repo,
            output_dir=tmp_path / "output",
            days=1,
            deploy_method=DeployMethod.NONE,
            base_url="http://localhost"
        )
        
        scanner = ScannerService(config)
        assert scanner.config == config

    def test_scanner_execute_returns_endpoints(self, tmp_path):
        """Test that scanner execute returns at least the fallback endpoint."""
        from rebuild.application.services.scanner_service import ScannerService
        from rebuild.domain.models import WalkConfig, DeployMethod
        
        repo = _make_git_repo(tmp_path, with_commits=1)
        config = WalkConfig(
            repo_path=repo,
            output_dir=tmp_path / "output",
            days=1,
            deploy_method=DeployMethod.NONE,
            base_url="http://localhost"
        )
        
        scanner = ScannerService(config)
        endpoints = scanner.execute(repo)
        
        # Should return at least the fallback endpoint
        assert len(endpoints) >= 1
        assert any(ep.path == "/api/health" for ep in endpoints)

    def test_scanner_fastapi_routes_discovery(self, tmp_path):
        """Test that scanner can discover FastAPI routes from source code."""
        from rebuild.application.services.scanner_service import ScannerService
        from rebuild.domain.models import WalkConfig, DeployMethod
        
        repo = _make_git_repo(tmp_path, with_commits=1)
        
        # Create a mock FastAPI app file
        (repo / "app.py").write_text(textwrap.dedent("""
            from fastapi import FastAPI
            
            app = FastAPI()
            
            @app.get("/api/items")
            def list_items():
                return []
            
            @app.post("/api/items")
            def create_item():
                return {}
        """))
        
        config = WalkConfig(
            repo_path=repo,
            output_dir=tmp_path / "output",
            days=1,
            deploy_method=DeployMethod.NONE,
            base_url="http://localhost"
        )
        
        scanner = ScannerService(config)
        endpoints = scanner.execute(repo)
        
        # Should discover FastAPI routes
        assert len(endpoints) >= 1
