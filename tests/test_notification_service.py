"""
Tests for NotificationService — webhook dispatch, payload builders, from_config.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.application.services.notification_service import (
    NotificationEvent,
    NotificationPayload,
    NotificationService,
    WebhookConfig,
    _build_discord_payload,
    _build_generic_payload,
    _build_slack_payload,
    _send_webhook,
)


# ─── payload builders ────────────────────────────────────────────────────────

class TestPayloadBuilders:
    def _payload(self, severity="info"):
        return NotificationPayload(
            event=NotificationEvent.WALK_COMPLETE,
            message="Walk done",
            details={"days": 7, "healthy": 5},
            severity=severity,
        )

    def test_slack_has_attachments(self):
        body = _build_slack_payload(self._payload())
        assert "attachments" in body
        assert body["attachments"][0]["text"] == "Walk done"
        assert "days" in str(body["attachments"][0]["fields"])

    def test_slack_error_color(self):
        body = _build_slack_payload(self._payload(severity="error"))
        assert body["attachments"][0]["color"] == "#cc0000"

    def test_slack_warning_color(self):
        body = _build_slack_payload(self._payload(severity="warning"))
        assert body["attachments"][0]["color"] == "#ffa500"

    def test_discord_has_embeds(self):
        body = _build_discord_payload(self._payload())
        assert "embeds" in body
        assert body["embeds"][0]["description"] == "Walk done"

    def test_discord_error_color(self):
        body = _build_discord_payload(self._payload(severity="error"))
        assert body["embeds"][0]["color"] == 0xCC0000

    def test_generic_has_event_and_message(self):
        body = _build_generic_payload(self._payload())
        assert body["event"] == "walk_complete"
        assert body["message"] == "Walk done"
        assert body["details"]["days"] == 7
        assert body["severity"] == "info"


# ─── _send_webhook ────────────────────────────────────────────────────────────

class TestSendWebhook:
    def test_success_returns_true(self):
        cfg = WebhookConfig(url="http://example.com/hook")
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("rebuild.application.services.notification_service.urllib.request.urlopen",
                   return_value=mock_resp):
            assert _send_webhook(cfg, {"msg": "hi"}) is True

    def test_url_error_returns_false(self):
        import urllib.error
        cfg = WebhookConfig(url="http://bad.example.com/hook")
        with patch("rebuild.application.services.notification_service.urllib.request.urlopen",
                   side_effect=urllib.error.URLError("connection refused")):
            assert _send_webhook(cfg, {"msg": "hi"}) is False

    def test_exception_returns_false(self):
        cfg = WebhookConfig(url="http://example.com/hook")
        with patch("rebuild.application.services.notification_service.urllib.request.urlopen",
                   side_effect=Exception("boom")):
            assert _send_webhook(cfg, {"msg": "hi"}) is False

    def test_http_400_returns_false(self):
        cfg = WebhookConfig(url="http://example.com/hook")
        mock_resp = MagicMock()
        mock_resp.status = 400
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("rebuild.application.services.notification_service.urllib.request.urlopen",
                   return_value=mock_resp):
            assert _send_webhook(cfg, {"msg": "hi"}) is False


# ─── NotificationService ──────────────────────────────────────────────────────

class TestNotificationService:
    def _svc_with_mock(self, platform="generic"):
        svc = NotificationService()
        cfg = WebhookConfig(url="http://example.com/hook", platform=platform)
        svc.add_webhook(cfg)
        return svc

    def _mock_send(self, ok=True):
        return patch(
            "rebuild.application.services.notification_service._send_webhook",
            return_value=ok,
        )

    def test_notify_reaches_hook(self):
        svc = self._svc_with_mock()
        with self._mock_send(True) as mock_send:
            results = svc.notify(NotificationPayload(
                event=NotificationEvent.WALK_COMPLETE,
                message="done",
            ))
        assert results == [True]
        mock_send.assert_called_once()

    def test_disabled_hook_skipped(self):
        svc = NotificationService()
        svc.add_webhook(WebhookConfig(url="http://x.com/h", enabled=False))
        with self._mock_send(True) as mock_send:
            results = svc.notify(NotificationPayload(
                event=NotificationEvent.WALK_COMPLETE, message="done"
            ))
        assert results == [False]
        mock_send.assert_not_called()

    def test_event_filter(self):
        svc = NotificationService()
        svc.add_webhook(WebhookConfig(
            url="http://x.com/h",
            events=[NotificationEvent.DEPLOY_FAIL.value],
        ))
        with self._mock_send(True) as mock_send:
            results = svc.notify(NotificationPayload(
                event=NotificationEvent.WALK_COMPLETE, message="done"
            ))
        assert results == [False]
        mock_send.assert_not_called()

    def test_multiple_hooks(self):
        svc = NotificationService()
        svc.add_webhook(WebhookConfig(url="http://a.com/h"))
        svc.add_webhook(WebhookConfig(url="http://b.com/h"))
        with self._mock_send(True):
            results = svc.notify(NotificationPayload(
                event=NotificationEvent.WALK_COMPLETE, message="done"
            ))
        assert len(results) == 2

    def test_remove_webhook(self):
        svc = self._svc_with_mock()
        svc.remove_webhook("http://example.com/hook")
        assert svc.hooks == []

    def test_clear(self):
        svc = self._svc_with_mock()
        svc.clear()
        assert svc.hooks == []

    def test_notify_deploy_fail(self):
        svc = self._svc_with_mock()
        with self._mock_send(True) as mock_send:
            svc.notify_deploy_fail(date(2025, 1, 1), "abc12345def", "timeout")
        call_args = mock_send.call_args[0]
        body = call_args[1]
        assert "deploy_fail" in body["event"]
        assert "2025-01-01" in body["message"]

    def test_notify_health_regression(self):
        svc = self._svc_with_mock()
        with self._mock_send(True) as mock_send:
            svc.notify_health_regression(date(2025, 1, 5), 95.0, 50.0, "abc")
        body = mock_send.call_args[0][1]
        assert "health_regression" in body["event"]
        assert "95" in body["message"]
        assert "50" in body["message"]
        assert "-45" in body["details"]["delta"]

    def test_notify_walk_complete(self):
        svc = self._svc_with_mock()
        with self._mock_send(True) as mock_send:
            svc.notify_walk_complete(14, 12, 87.5, Path("/out"))
        body = mock_send.call_args[0][1]
        assert "walk_complete" in body["event"]
        assert "12/14" in body["message"]
        assert "87" in body["message"] or "88" in body["message"]

    def test_slack_platform_uses_attachments(self):
        svc = self._svc_with_mock(platform="slack")
        captured = {}
        def capture(cfg, body):
            captured["body"] = body
            return True
        with patch("rebuild.application.services.notification_service._send_webhook", side_effect=capture):
            svc.notify(NotificationPayload(
                event=NotificationEvent.WALK_COMPLETE, message="done"
            ))
        assert "attachments" in captured["body"]

    def test_discord_platform_uses_embeds(self):
        svc = self._svc_with_mock(platform="discord")
        captured = {}
        def capture(cfg, body):
            captured["body"] = body
            return True
        with patch("rebuild.application.services.notification_service._send_webhook", side_effect=capture):
            svc.notify(NotificationPayload(
                event=NotificationEvent.WALK_COMPLETE, message="done"
            ))
        assert "embeds" in captured["body"]


# ─── from_config ──────────────────────────────────────────────────────────────

class TestFromConfig:
    def test_empty_list(self):
        svc = NotificationService.from_config([])
        assert svc.hooks == []

    def test_single_slack_hook(self):
        cfg = [{"url": "https://hooks.slack.com/xxx", "platform": "slack"}]
        svc = NotificationService.from_config(cfg)
        assert len(svc.hooks) == 1
        assert svc.hooks[0].platform == "slack"
        assert svc.hooks[0].url == "https://hooks.slack.com/xxx"

    def test_disabled_hook(self):
        cfg = [{"url": "https://hooks.slack.com/xxx", "enabled": False}]
        svc = NotificationService.from_config(cfg)
        assert svc.hooks[0].enabled is False

    def test_event_filter_from_config(self):
        cfg = [{"url": "http://x.com/h", "events": ["deploy_fail"]}]
        svc = NotificationService.from_config(cfg)
        assert svc.hooks[0].events == ["deploy_fail"]

    def test_extra_headers(self):
        cfg = [{"url": "http://x.com/h", "headers": {"X-Token": "abc"}}]
        svc = NotificationService.from_config(cfg)
        assert svc.hooks[0].extra_headers["X-Token"] == "abc"

    def test_timeout_from_config(self):
        cfg = [{"url": "http://x.com/h", "timeout": 30}]
        svc = NotificationService.from_config(cfg)
        assert svc.hooks[0].timeout_seconds == 30

    def test_invalid_item_skipped(self):
        cfg = [{"no_url": "x"}, {"url": "http://x.com/h"}]
        svc = NotificationService.from_config(cfg)
        assert len(svc.hooks) == 1

    def test_non_dict_item_skipped(self):
        cfg = ["http://x.com/h", {"url": "http://y.com/h"}]
        svc = NotificationService.from_config(cfg)
        assert len(svc.hooks) == 1


# ─── ConfigLoader integration ─────────────────────────────────────────────────

class TestConfigLoaderNotifications:
    def test_notifications_loaded_from_yaml(self, tmp_path):
        from rebuild.infrastructure.config_loader import ConfigLoader
        from rebuild.domain.models import WalkConfig
        data = {
            "project": {
                "days": 7,
                "notifications": [
                    {"url": "https://hooks.slack.com/xxx", "platform": "slack"},
                    {"url": "https://discord.com/api/webhooks/yyy", "platform": "discord"},
                ],
            }
        }
        config = WalkConfig(repo_path=tmp_path)
        ConfigLoader.apply_to_config(config, data)
        assert len(config.notifications) == 2
        assert config.notifications[0]["platform"] == "slack"
        assert config.notifications[1]["platform"] == "discord"

    def test_notifications_root_level(self, tmp_path):
        from rebuild.infrastructure.config_loader import ConfigLoader
        from rebuild.domain.models import WalkConfig
        data = {
            "project": {"days": 7},
            "notifications": [{"url": "http://example.com/hook"}],
        }
        config = WalkConfig(repo_path=tmp_path)
        ConfigLoader.apply_to_config(config, data)
        assert len(config.notifications) == 1

    def test_no_notifications_defaults_empty(self, tmp_path):
        from rebuild.infrastructure.config_loader import ConfigLoader
        from rebuild.domain.models import WalkConfig
        config = WalkConfig(repo_path=tmp_path)
        ConfigLoader.apply_to_config(config, {"project": {"days": 7}})
        assert config.notifications == []
