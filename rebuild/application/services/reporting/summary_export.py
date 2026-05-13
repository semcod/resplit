"""Plain-text summary exporters (CSV, Markdown).

Pure functions extracted from :class:`ReporterService` (Sprint 5b / 2026-05-08).
Both writers consume already-validated ``DayResult`` objects and use the
canonical :mod:`regression_service` / :mod:`endpoint_trend_service` for trend
labels — they never duplicate the threshold logic.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import TYPE_CHECKING, List

from ..endpoint_trend_service import compute_endpoint_count_trend_dict
from ..regression_service import compute_health_trend_dict

if TYPE_CHECKING:
    from ....domain.day_result import DayResult


def write_csv(results: List["DayResult"], output_dir: Path) -> Path:
    """Write ``summary.csv`` with one row per day. Returns the destination path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "summary.csv"
    rows = sorted(results, key=lambda x: x.day)
    trend_by_day = compute_health_trend_dict(rows)
    endpoint_trend_by_day = compute_endpoint_count_trend_dict(rows)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "day",
            "commit",
            "health_pct",
            "health_trend",
            "ok",
            "fail",
            "total",
            "endpoint_count_trend",
            "deploy_success",
            "deploy_error_category",
            "duration_seconds",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                str(r.day),
                r.commit.sha[:8] if r.commit else "",
                r.health_pct,
                trend_by_day.get(str(r.day), "—"),
                r.ok_count,
                r.fail_count,
                len(r.endpoints),
                endpoint_trend_by_day.get(str(r.day), "—"),
                "true" if r.deploy_success else "false",
                r.deploy_error_category.value if r.deploy_error_category else "",
                round(r.duration_seconds, 2),
            ]
        )
    dest.write_text(buf.getvalue(), encoding="utf-8")
    return dest


def write_markdown(results: List["DayResult"], output_dir: Path) -> Path:
    """Write ``summary.md`` with a Markdown table of walk results."""
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "summary.md"
    rows = sorted(results, key=lambda x: x.day)
    trend_by_day = compute_health_trend_dict(rows)
    endpoint_trend_by_day = compute_endpoint_count_trend_dict(rows)
    lines = [
        "# rebuild walk summary",
        "",
        "| Day | Commit | Health | Trend | OK | Fail | Total | EP Δ | Deploy | Duration |",
        "|-----|--------|--------|-------|----|------|-------|------|--------|----------|",
    ]
    for r in rows:
        dep = "✓" if r.deploy_success else "✗"
        cat = (
            f" ({r.deploy_error_category.value})"
            if r.deploy_error_category and not r.deploy_success
            else ""
        )
        lines.append(
            f"| {r.day} "
            f"| `{r.commit.sha[:8] if r.commit else '—'}` "
            f"| {r.health_pct}% "
            f"| {trend_by_day.get(str(r.day), '—')} "
            f"| {r.ok_count} "
            f"| {r.fail_count} "
            f"| {len(r.endpoints)} "
            f"| {endpoint_trend_by_day.get(str(r.day), '—')} "
            f"| {dep}{cat} "
            f"| {r.duration_seconds:.1f}s |"
        )
    lines.append("")
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest
