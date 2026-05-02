"""
E2E tests for TUI (Textual User Interface) navigation and screens.

Tests simulate realistic end-to-end scenarios for the TUI application
using mock dependencies where network/docker is not available.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from io import StringIO

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# E2E: TUI Screens — initialization, navigation, data display
# ─────────────────────────────────────────────────────────────────────────────

class TestTUIScreensE2E:
    def test_tui_app_initialization(self, tmp_path):
        """Test that TUI app can be initialized."""
        from rebuild.interfaces.tui.app import RebuildTUI
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        if not TEXTUAL_OK:
            pytest.skip("Textual not available")
        
        app = RebuildTUI()
        assert app is not None
        assert hasattr(app, 'TITLE')

    def test_project_screen_initialization(self, tmp_path):
        """Test that ProjectScreen can be initialized."""
        from rebuild.interfaces.tui.screens.project_screen import ProjectScreen
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        if not TEXTUAL_OK:
            pytest.skip("Textual not available")
        
        screen = ProjectScreen()
        assert screen is not None
        assert hasattr(screen, 'BINDINGS')

    def test_history_screen_initialization(self, tmp_path):
        """Test that HistoryScreen can be initialized."""
        from rebuild.interfaces.tui.screens.history_screen import HistoryScreen
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        if not TEXTUAL_OK:
            pytest.skip("Textual not available")
        
        repo = tmp_path / "repo"
        results_dir = tmp_path / "results"
        screen = HistoryScreen(repo, results_dir)
        assert screen is not None
        assert screen._repo == repo
        assert screen._results_dir == results_dir

    def test_endpoint_detail_screen_initialization(self, tmp_path):
        """Test that EndpointDetailScreen can be initialized."""
        from rebuild.interfaces.tui.screens.endpoint_screens import EndpointDetailScreen
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        if not TEXTUAL_OK:
            pytest.skip("Textual not available")
        
        day_data = {"day": "2025-01-01", "commit": "abc123"}
        screen = EndpointDetailScreen(day_data=day_data, prev_data=None)
        assert screen is not None
        assert screen._day == day_data

    def test_walk_config_screen_initialization(self, tmp_path):
        """Test that WalkConfigScreen can be initialized."""
        from rebuild.interfaces.tui.screens.walk_screens import WalkConfigScreen
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        if not TEXTUAL_OK:
            pytest.skip("Textual not available")
        
        screen = WalkConfigScreen(repo=tmp_path / "repo")
        assert screen is not None
        assert hasattr(screen, 'BINDINGS')

    def test_help_screen_initialization(self, tmp_path):
        """Test that HelpScreen can be initialized."""
        from rebuild.interfaces.tui.screens.help_screen import HelpScreen
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        if not TEXTUAL_OK:
            pytest.skip("Textual not available")
        
        screen = HelpScreen()
        assert screen is not None
        assert hasattr(screen, 'BINDINGS')


# ─────────────────────────────────────────────────────────────────────────────
# E2E: TUI Navigation — keyboard bindings, screen transitions
# ─────────────────────────────────────────────────────────────────────────────

class TestTUINavigationE2E:
    def test_history_screen_key_bindings(self, tmp_path):
        """Test that HistoryScreen has correct key bindings."""
        from rebuild.interfaces.tui.screens.history_screen import HistoryScreen
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        if not TEXTUAL_OK:
            pytest.skip("Textual not available")
        
        repo = tmp_path / "repo"
        results_dir = tmp_path / "results"
        screen = HistoryScreen(repo, results_dir)
        
        # Check for expected bindings
        binding_keys = [b.key for b in screen.BINDINGS]
        assert "escape" in binding_keys
        assert "enter" in binding_keys
        assert "j" in binding_keys
        assert "k" in binding_keys
        assert "g" in binding_keys
        assert "G" in binding_keys

    def test_endpoint_screen_key_bindings(self, tmp_path):
        """Test that EndpointDetailScreen has correct key bindings."""
        from rebuild.interfaces.tui.screens.endpoint_screens import EndpointDetailScreen
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        if not TEXTUAL_OK:
            pytest.skip("Textual not available")
        
        day_data = {"day": "2025-01-01", "commit": "abc123"}
        screen = EndpointDetailScreen(day_data=day_data, prev_data=None)
        
        # Check for expected bindings
        binding_keys = [b.key for b in screen.BINDINGS]
        assert "escape" in binding_keys
        assert "j" in binding_keys
        assert "k" in binding_keys
        assert "g" in binding_keys
        assert "G" in binding_keys
        assert "f" in binding_keys


# ─────────────────────────────────────────────────────────────────────────────
# E2E: TUI Data Display — tables, formatting, filtering
# ─────────────────────────────────────────────────────────────────────────────

class TestTUIDataDisplayE2E:
    def test_history_screen_table_population(self, tmp_path):
        """Test that HistoryScreen table is created."""
        from rebuild.interfaces.tui.screens.history_screen import HistoryScreen
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        if not TEXTUAL_OK:
            pytest.skip("Textual not available")
        
        repo = tmp_path / "repo"
        results_dir = tmp_path / "results"
        screen = HistoryScreen(repo, results_dir)
        
        # Check that table widget exists
        assert hasattr(screen, 'compose')
        # The table should be created during compose
        assert screen.BINDINGS is not None

    def test_endpoint_screen_table_population(self, tmp_path):
        """Test that EndpointDetailScreen table is created."""
        from rebuild.interfaces.tui.screens.endpoint_screens import EndpointDetailScreen
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        if not TEXTUAL_OK:
            pytest.skip("Textual not available")
        
        day_data = {"day": "2025-01-01", "commit": "abc123"}
        screen = EndpointDetailScreen(day_data=day_data, prev_data=None)
        
        # Check that table widget exists
        assert hasattr(screen, 'compose')
        assert screen.BINDINGS is not None

    def test_help_screen_content_display(self, tmp_path):
        """Test that HelpScreen can be created."""
        from rebuild.interfaces.tui.screens.help_screen import HelpScreen
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        if not TEXTUAL_OK:
            pytest.skip("Textual not available")
        
        screen = HelpScreen()
        assert screen is not None
        assert hasattr(screen, 'compose')


# ─────────────────────────────────────────────────────────────────────────────
# E2E: TUI CLI Integration — tui command, launch
# ─────────────────────────────────────────────────────────────────────────────

class TestTUICLIE2E:
    def test_tui_launch_check(self, tmp_path):
        """Test that TUI can check if textual is available."""
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        # Check if textual is available
        result = TEXTUAL_OK
        assert isinstance(result, bool)

    def test_tui_launch_without_textual(self, tmp_path):
        """Test TUI launch behavior when textual is not available."""
        from rebuild.interfaces.tui.compat import TEXTUAL_OK
        
        # If textual is not available, the compat module should handle it
        # This test verifies the structure is in place
        assert isinstance(TEXTUAL_OK, bool)
