"""
E2E tests for Notification service (webhooks) and Snapshot management (LRU cache).

Tests simulate realistic end-to-end scenarios using mock dependencies
where network/docker is not available.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from io import StringIO

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# E2E: Notification Service — webhooks, event publishing
# ─────────────────────────────────────────────────────────────────────────────

class TestNotificationServiceE2E:
    def test_notification_service_initialization(self, tmp_path):
        """Test that NotificationService can be initialized."""
        from rebuild.application.services.notification_service import NotificationService
        
        service = NotificationService()
        assert service is not None
        assert service.hooks == []


# ─────────────────────────────────────────────────────────────────────────────
# E2E: Snapshot Management — LRU cache, DB snapshots
# ─────────────────────────────────────────────────────────────────────────────

class TestSnapshotManagementE2E:
    def test_db_snapshot_manager_initialization(self, tmp_path):
        """Test that DBSnapshotManager can be initialized."""
        from rebuild.application.services.db_snapshot_manager import DBSnapshotManager
        
        snapshot_dir = tmp_path / "snapshots"
        snapshot_dir.mkdir()
        
        manager = DBSnapshotManager(snapshot_dir)
        assert manager.snapshot_dir == snapshot_dir
        assert manager.db_type == "postgres"

    def test_db_snapshot_manager_create_snapshot_info(self, tmp_path):
        """Test that SnapshotInfo can be created."""
        from rebuild.application.services.db_snapshot_manager import SnapshotInfo
        
        info = SnapshotInfo(
            name="test_snapshot",
            created_at="2025-01-01T00:00:00",
            commit_sha="abc123",
            db_type="postgres"
        )
        
        assert info.name == "test_snapshot"
        assert info.db_type == "postgres"


# ─────────────────────────────────────────────────────────────────────────────
# E2E: Event Sourcing — event bus, history.jsonl
# ─────────────────────────────────────────────────────────────────────────────

class TestEventSourcingE2E:
    def test_event_service_initialization(self, tmp_path):
        """Test that EventService can be initialized."""
        from rebuild.application.services.event_service import EventService
        
        service = EventService()
        assert service is not None

    def test_pipeline_event_creation(self, tmp_path):
        """Test that PipelineEvent can be created."""
        from rebuild.application.services.event_service import PipelineEvent, EventType
        
        event = PipelineEvent(
            event_type=EventType.PIPELINE_START,
            timestamp="2025-01-01T00:00:00",
            data={"days": 5},
            day="2025-01-01",
            commit="abc123"
        )
        
        assert event.event_type == EventType.PIPELINE_START
        assert event.day == "2025-01-01"

    def test_pipeline_event_to_sse(self, tmp_path):
        """Test that PipelineEvent can be converted to SSE format."""
        from rebuild.application.services.event_service import PipelineEvent, EventType
        
        event = PipelineEvent(
            event_type=EventType.PIPELINE_START,
            timestamp="2025-01-01T00:00:00",
            data={"days": 5},
        )
        
        sse_format = event.to_sse()
        
        assert "data:" in sse_format
        assert "pipeline_start" in sse_format
        assert "days" in sse_format
