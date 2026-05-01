from __future__ import annotations

from typing import Any, Dict, List

from ....domain.day_result import DayResult
from ....domain.endpoint import EndpointResult, EndpointStatus


def to_yaml(data: Dict[str, Any], indent: int = 0) -> str:
    lines = []
    space = "  " * indent
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"{space}{k}:")
            lines.append(to_yaml(v, indent + 1))
        elif isinstance(v, list):
            lines.append(f"{space}{k}:")
            for item in v:
                if isinstance(item, dict):
                    lines.append(f"{space}-")
                    lines.append(to_yaml(item, indent + 1))
                else:
                    lines.append(f"{space}- {item}")
        else:
            lines.append(f"{space}{k}: {v}")
    return "\n".join(lines)


def to_toon(result: DayResult) -> str:
    lines = [
        f"type: rebuild_report",
        f"day: {result.day}",
        f"health: {result.health_pct}%",
        f"stats: {result.ok_count}/{len(result.endpoints)}",
        f"deploy: {'success' if result.deploy_success else 'failed'}",
        f"mode: {'dry-run' if result.is_dry_run else 'live'}",
        "---",
    ]
    for r in result.endpoint_results:
        err = f" ({r.error})" if r.error else ""
        lines.append(f"{r.endpoint.method} {r.endpoint.path} [{r.status.value}] {r.http_status or ''}{err}")
    return "\n".join(lines)


def status_badge(status: EndpointStatus) -> str:
    colors = {
        EndpointStatus.OK: ("#22c55e", "✓ OK"),
        EndpointStatus.FAIL: ("#ef4444", "✗ FAIL"),
        EndpointStatus.FAIL_AUTH: ("#f97316", "✗ AUTH"),
        EndpointStatus.FAIL_SERVER: ("#ef4444", "✗ 5xx"),
        EndpointStatus.FAIL_NETWORK: ("#f97316", "✗ NET"),
        EndpointStatus.FAIL_TEMPLATE: ("#f59e0b", "✗ TMPL"),
        EndpointStatus.TIMEOUT: ("#f97316", "⏱ TIMEOUT"),
        EndpointStatus.SKIP: ("#94a3b8", "– SKIP"),
        EndpointStatus.SKIP_METHOD: ("#94a3b8", "– METHOD"),
        EndpointStatus.SKIP_AUTH: ("#94a3b8", "– AUTH"),
    }
    color, label = colors.get(status, ("#94a3b8", status.value))
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{label}</span>'


def classify_error(result: EndpointResult) -> str:
    if result.status == EndpointStatus.OK or result.status == EndpointStatus.SKIP:
        return ""
    if result.status == EndpointStatus.FAIL_AUTH:
        return "auth"
    if result.status == EndpointStatus.FAIL_TEMPLATE:
        return "template"
    if result.status == EndpointStatus.FAIL_NETWORK:
        return "network"
    if result.status == EndpointStatus.FAIL_SERVER:
        return "server"
    if not result.error:
        return "unknown"
    err_lower = result.error.lower()
    if any(k in err_lower for k in ["unauthorized", "401", "forbidden", "403", "auth", "token"]):
        return "auth"
    if any(k in err_lower for k in ["not found", "404", "missing", "template", "param"]):
        return "template"
    if "timeout" in err_lower:
        return "timeout"
    if any(k in err_lower for k in ["500", "internal", "server error"]):
        return "server"
    if any(k in err_lower for k in ["connection", "network", "refused"]):
        return "network"
    return "other"
