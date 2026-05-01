from __future__ import annotations

from typing import List

from ....domain.day_result import DayResult


def generate_trend_chart(results: List[DayResult]) -> str:
    if not results:
        return ""
    sorted_results = sorted(results, key=lambda x: x.day)
    width, height, padding = 800, 120, 30
    plot_width = width - 2 * padding
    plot_height = height - 2 * padding

    points = []
    for i, r in enumerate(sorted_results):
        x = padding + (i / max(1, len(sorted_results) - 1)) * plot_width
        y = padding + (1 - r.health_pct / 100) * plot_height
        points.append(f"{x},{y}")

    if not points:
        return ""

    polyline = " ".join(points)
    avg_health = sum(r.health_pct for r in sorted_results) / len(sorted_results)
    stroke_color = "#22c55e" if avg_health >= 80 else "#f97316" if avg_health >= 50 else "#ef4444"

    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" style="background:#f8fafc;border-radius:8px;margin:24px 0;">'
        f'<line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" stroke="#cbd5e1" stroke-width="1"/>'
        f'<line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#cbd5e1" stroke-width="1"/>'
        f'<text x="{padding-5}" y="{padding}" text-anchor="end" font-size="10" fill="#64748b">100%</text>'
        f'<text x="{padding-5}" y="{height-padding}" text-anchor="end" font-size="10" fill="#64748b">0%</text>'
        f'<polyline points="{polyline}" fill="none" stroke="{stroke_color}" stroke-width="2" stroke-linejoin="round"/>'
        + "".join(
            f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="3" fill="{stroke_color}"/>'
            for p in points
        )
        + "</svg>"
    )


def generate_endpoint_diff(results: List[DayResult]) -> str:
    if len(results) < 2:
        return ""
    sorted_results = sorted(results, key=lambda x: x.day)
    diff_rows = ""
    for i in range(1, len(sorted_results)):
        prev = sorted_results[i - 1]
        curr = sorted_results[i]
        prev_eps = {f"{ep.method} {ep.path}" for ep in prev.endpoints}
        curr_eps = {f"{ep.method} {ep.path}" for ep in curr.endpoints}
        added = curr_eps - prev_eps
        removed = prev_eps - curr_eps
        if not added and not removed:
            continue
        diff_rows += (
            f'<div class="diff-item">'
            f'<div style="font-weight:700;color:var(--text);margin-bottom:4px;">{prev.day} → {curr.day}</div>'
            + (f'<div style="color:var(--success)">+ {len(added)} added: {", ".join(sorted(added)[:2])}{"..." if len(added) > 2 else ""}</div>' if added else "")
            + (f'<div style="color:var(--fail)">- {len(removed)} removed: {", ".join(sorted(removed)[:2])}{"..." if len(removed) > 2 else ""}</div>' if removed else "")
            + "</div>"
        )
    if not diff_rows:
        return ""
    return f'<div style="margin:24px 0;"><h3 style="margin:0 0 12px 0;font-size:16px;">Endpoint Changes</h3>{diff_rows}</div>'
