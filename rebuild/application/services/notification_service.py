"""
Notification hooks for rebuild events.

Supports:
  - Slack (incoming webhook)
  - Discord (webhook)
  - Generic HTTP webhook (JSON POST)
  - Multiple hooks simultaneously

Triggered on:
  - deploy failure
  - health regression (configurable threshold)
  - walk completion summary
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NotificationEvent(str, Enum):
    DEPLOY_FAIL = "deploy_fail"
    HEALTH_REGRESSION = "health_regression"
    WALK_COMPLETE = "walk_complete"
    WALK_ERROR = "walk_error"


@dataclass
class NotificationPayload:
    event: NotificationEvent
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info | warning | error


@dataclass
class WebhookConfig:
    url: str
    platform: str = "generic"  # slack | discord | generic
    enabled: bool = True
    events: List[str] = field(default_factory=lambda: [e.value for e in NotificationEvent])
    extra_headers: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 10


def _build_slack_payload(payload: NotificationPayload) -> Dict[str, Any]:
    icon = {"info": ":information_source:", "warning": ":warning:", "error": ":rotating_light:"}
    color = {"info": "#36a64f", "warning": "#ffa500", "error": "#cc0000"}
    return {
        "attachments": [
            {
                "color": color.get(payload.severity, "#36a64f"),
                "pretext": f"{icon.get(payload.severity, '')} *rebuild* — {payload.event.value}",
                "text": payload.message,
                "fields": [
                    {"title": k, "value": str(v), "short": True} for k, v in payload.details.items()
                ],
                "footer": "rebuild",
            }
        ]
    }


def _build_discord_payload(payload: NotificationPayload) -> Dict[str, Any]:
    color_map = {"info": 0x36A64F, "warning": 0xFFA500, "error": 0xCC0000}
    return {
        "embeds": [
            {
                "title": f"rebuild — {payload.event.value}",
                "description": payload.message,
                "color": color_map.get(payload.severity, 0x36A64F),
                "fields": [
                    {"name": k, "value": str(v), "inline": True} for k, v in payload.details.items()
                ],
            }
        ]
    }


def _build_generic_payload(payload: NotificationPayload) -> Dict[str, Any]:
    return {
        "event": payload.event.value,
        "message": payload.message,
        "severity": payload.severity,
        "details": payload.details,
    }


def _send_webhook(cfg: WebhookConfig, body: Dict[str, Any]) -> bool:
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json", **cfg.extra_headers}
    req = urllib.request.Request(cfg.url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_seconds) as resp:
            return resp.status < 400
    except urllib.error.URLError as exc:
        logger.warning("Webhook to %r failed: %s", cfg.url, exc)
        return False
    except Exception as exc:
        logger.warning("Webhook to %r unexpected error: %s", cfg.url, exc)
        return False


class NotificationService:
    """
    Send webhook notifications on rebuild events.

    Usage::

        svc = NotificationService()
        svc.add_webhook(WebhookConfig(url="https://hooks.slack.com/...", platform="slack"))
        svc.add_webhook(WebhookConfig(url="https://discord.com/api/...", platform="discord"))

        svc.notify(NotificationPayload(
            event=NotificationEvent.DEPLOY_FAIL,
            message="Deploy failed for commit abc123",
            details={"day": "2025-01-15", "commit": "abc123"},
            severity="error",
        ))
    """

    def __init__(self) -> None:
        self._hooks: List[WebhookConfig] = []

    def add_webhook(self, cfg: WebhookConfig) -> None:
        self._hooks.append(cfg)

    def remove_webhook(self, url: str) -> None:
        self._hooks = [h for h in self._hooks if h.url != url]

    def clear(self) -> None:
        self._hooks.clear()

    @property
    def hooks(self) -> List[WebhookConfig]:
        return list(self._hooks)

    def notify(self, payload: NotificationPayload) -> List[bool]:
        """Send *payload* to all matching hooks. Returns per-hook success list."""
        results: List[bool] = []
        for cfg in self._hooks:
            if not cfg.enabled:
                results.append(False)
                continue
            if payload.event.value not in cfg.events:
                results.append(False)
                continue
            body = self._build_body(cfg, payload)
            ok = _send_webhook(cfg, body)
            results.append(ok)
            if ok:
                logger.debug("Notification sent to %r (%s)", cfg.url, payload.event.value)
        return results

    def notify_deploy_fail(
        self, day: Any, commit: Optional[str], error: Optional[str] = None
    ) -> List[bool]:
        return self.notify(
            NotificationPayload(
                event=NotificationEvent.DEPLOY_FAIL,
                message=f"Deploy failed for {day}" + (f" @ {commit[:8]}" if commit else ""),
                details={"day": str(day), "commit": commit or "—", "error": error or "—"},
                severity="error",
            )
        )

    def notify_health_regression(
        self,
        day: Any,
        from_pct: float,
        to_pct: float,
        commit: Optional[str] = None,
    ) -> List[bool]:
        delta = round(to_pct - from_pct, 1)
        return self.notify(
            NotificationPayload(
                event=NotificationEvent.HEALTH_REGRESSION,
                message=f"Health regression on {day}: {from_pct:.0f}% → {to_pct:.0f}% ({delta:+.1f}pp)",
                details={
                    "day": str(day),
                    "from": f"{from_pct:.1f}%",
                    "to": f"{to_pct:.1f}%",
                    "delta": f"{delta:+.1f}pp",
                    "commit": commit or "—",
                },
                severity="warning",
            )
        )

    def notify_walk_complete(
        self,
        total_days: int,
        healthy_days: int,
        avg_health_pct: float,
        output_dir: Optional[Path] = None,
    ) -> List[bool]:
        return self.notify(
            NotificationPayload(
                event=NotificationEvent.WALK_COMPLETE,
                message=f"Walk complete: {healthy_days}/{total_days} days healthy, avg {avg_health_pct:.0f}%",
                details={
                    "total_days": total_days,
                    "healthy_days": healthy_days,
                    "avg_health": f"{avg_health_pct:.1f}%",
                    "output": str(output_dir) if output_dir else "—",
                },
                severity="info",
            )
        )

    @staticmethod
    def _build_body(cfg: WebhookConfig, payload: NotificationPayload) -> Dict[str, Any]:
        if cfg.platform == "slack":
            return _build_slack_payload(payload)
        if cfg.platform == "discord":
            return _build_discord_payload(payload)
        return _build_generic_payload(payload)

    @classmethod
    def from_config(cls, config: List[Dict[str, Any]]) -> "NotificationService":
        """Create a NotificationService from a list of webhook config dicts."""
        svc = cls()
        for item in config:
            if not isinstance(item, dict) or "url" not in item:
                continue
            cfg = WebhookConfig(
                url=item["url"],
                platform=item.get("platform", "generic"),
                enabled=bool(item.get("enabled", True)),
                events=item.get("events", [e.value for e in NotificationEvent]),
                extra_headers=item.get("headers", {}),
                timeout_seconds=int(item.get("timeout", 10)),
            )
            svc.add_webhook(cfg)
        return svc
