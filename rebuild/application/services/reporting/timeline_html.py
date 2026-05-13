"""Timeline / cross-day index HTML rendering.

Pure functions extracted from :class:`ReporterService` (Sprint 5b / 2026-05-08).
``render_timeline_html(results)`` produces the full ``index.html`` document;
``build_export_data(results)`` computes the JSON-friendly shape used by
``history.json`` and the in-page ``DATA`` blob.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, List

from ._html_assets import CSS_VARS
from .chart_builder import generate_endpoint_diff, generate_trend_chart

if TYPE_CHECKING:
    from ....domain.day_result import DayResult


def _trend_dicts(results_asc: List["DayResult"]) -> tuple[dict, dict]:
    """Return ``(health_trend_by_day, endpoint_trend_by_day)`` mappings."""
    from ..endpoint_trend_service import compute_endpoint_count_trend_dict
    from ..regression_service import compute_health_trend_dict

    health = compute_health_trend_dict(results_asc)
    endpoints = compute_endpoint_count_trend_dict(results_asc)
    return health, endpoints


def build_export_data(results: List["DayResult"]) -> list:
    """Build the JSON-serialisable list used by ``history.json`` and timeline JS."""
    sorted_asc = sorted(results, key=lambda x: x.day)
    trend_by_day, endpoint_trend_by_day = _trend_dicts(sorted_asc)
    return [
        {
            "day": str(r.day),
            "commit": r.commit.sha if r.commit else None,
            "commit_message": r.commit.message if r.commit else None,
            "health_pct": r.health_pct,
            "health_trend": trend_by_day.get(str(r.day), "—"),
            "health_regression": trend_by_day.get(str(r.day), "").startswith("⚠"),
            "endpoint_count_trend": endpoint_trend_by_day.get(str(r.day), "—"),
            "endpoint_count_warning": endpoint_trend_by_day.get(str(r.day), "").startswith("⚠"),
            "ok": r.ok_count,
            "fail": r.fail_count,
            "total": len(r.endpoints),
            "deploy_success": r.deploy_success,
            "deploy_error_category": r.deploy_error_category.value
            if r.deploy_error_category
            else None,
            "duration_seconds": r.duration_seconds,
        }
        for r in sorted(results, key=lambda x: x.day, reverse=True)
    ]


def _render_day_row(
    r: "DayResult",
    output_dir: Path,
    trend_by_day: dict,
    endpoint_trend_by_day: dict,
) -> str:
    day_dir = r.output_dir or (output_dir / str(r.day))
    rel = day_dir.relative_to(output_dir) if day_dir.is_relative_to(output_dir) else day_dir
    hc = (
        "var(--success)"
        if r.health_pct >= 80
        else "var(--warn)"
        if r.health_pct >= 50
        else "var(--fail)"
    )
    dep_cls = "tag-ok" if r.deploy_success else "tag-fail"
    dep_txt = "✓ OK" if r.deploy_success else "✗ FAIL"
    cat_txt = (
        f' <span style="color:var(--text-dim);font-size:0.75rem">({r.deploy_error_category.value})</span>'
        if r.deploy_error_category and not r.deploy_success
        else ""
    )
    trend = trend_by_day.get(str(r.day), "—")
    trend_html = (
        f' <span style="color:var(--fail);font-size:0.75rem">{trend}</span>'
        if trend.startswith("⚠")
        else f' <span style="color:var(--text-dim);font-size:0.75rem">{trend}</span>'
    )
    endpoint_trend = endpoint_trend_by_day.get(str(r.day), "—")
    endpoint_trend_html = (
        f' <span style="color:var(--warn);font-size:0.75rem">{endpoint_trend}</span>'
        if endpoint_trend.startswith("⚠")
        else f' <span style="color:var(--text-dim);font-size:0.75rem">{endpoint_trend}</span>'
    )
    return (
        f'<tr class="day-row">'
        f'<td><a href="{rel}/report.html" class="day-link">{r.day}</a></td>'
        f'<td><code class="commit-hash">{r.commit.sha[:8] if r.commit else "—"}</code></td>'
        f'<td><div class="health-bar-bg"><div class="health-bar-fill" style="width:{r.health_pct}%;background:{hc}"></div></div>'
        f'<span style="color:{hc};font-weight:700;font-size:0.85rem">{r.health_pct}%</span>{trend_html}</td>'
        f'<td><span class="stat-ok">{r.ok_count}</span> / <span class="stat-total">{len(r.endpoints)}</span>{endpoint_trend_html}</td>'
        f'<td><span class="deploy-tag {dep_cls}">{dep_txt}</span>{cat_txt}</td>'
        f"<td>{r.duration_seconds:.1f}s</td>"
        f"</tr>"
    )


def render_timeline_html(results: List["DayResult"], output_dir: Path) -> str:
    """Render the full ``index.html`` document for the cross-day timeline."""
    sorted_asc = sorted(results, key=lambda x: x.day)
    trend_by_day, endpoint_trend_by_day = _trend_dicts(sorted_asc)

    trend_svg = generate_trend_chart(results)
    diff_section = generate_endpoint_diff(results)
    export_data = build_export_data(results)
    export_js = json.dumps(export_data, ensure_ascii=False)

    rows = "".join(
        _render_day_row(r, output_dir, trend_by_day, endpoint_trend_by_day)
        for r in sorted(results, key=lambda x: x.day, reverse=True)
    )

    return f"""<!DOCTYPE html>
<html lang="pl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>rebuild — timeline</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{CSS_VARS}
  body{{font-family:'Outfit',sans-serif;margin:0;background:var(--bg);color:var(--text);min-height:100vh;}}
  nav{{background:rgba(15,23,42,0.8);backdrop-filter:blur(12px);padding:16px 32px;display:flex;align-items:center;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100;}}
  .brand{{font-weight:800;font-size:1.4rem;letter-spacing:-0.02em;}}
  .toolbar{{padding:16px 32px;display:flex;gap:12px;background:rgba(30,41,59,0.4);border-bottom:1px solid var(--border);overflow-x:auto;}}
  .btn{{padding:8px 16px;border-radius:8px;border:1px solid var(--border);background:rgba(255,255,255,0.05);color:var(--text);cursor:pointer;font-size:13px;font-weight:600;white-space:nowrap;}}
  .btn:hover{{background:rgba(255,255,255,0.1);}}
  .btn-primary{{background:var(--primary);border:none;}}
  .content{{padding:32px;max-width:1200px;margin:0 auto;}}
  .dashboard-grid{{display:grid;grid-template-columns:2fr 1fr;gap:24px;margin-bottom:40px;}}
  .glass-card{{background:var(--card-bg);border-radius:24px;border:1px solid var(--border);padding:24px;backdrop-filter:blur(8px);}}
  .table-container{{background:var(--card-bg);border-radius:24px;border:1px solid var(--border);overflow:hidden;}}
  table{{width:100%;border-collapse:collapse;text-align:left;}}
  th{{padding:20px 24px;background:rgba(15,23,42,0.4);font-size:0.75rem;font-weight:700;text-transform:uppercase;color:var(--text-dim);letter-spacing:0.1em;}}
  td{{padding:18px 24px;border-bottom:1px solid var(--border);}}
  .day-row:hover{{background:rgba(255,255,255,0.03);}}
  .day-link{{color:var(--text);text-decoration:none;font-weight:700;font-size:1.05rem;}}
  .day-link:hover{{color:var(--primary);}}
  .commit-hash{{font-family:'JetBrains Mono',monospace;color:var(--text-dim);font-size:0.85rem;}}
  .health-bar-bg{{width:100px;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;display:inline-block;margin-right:8px;vertical-align:middle;}}
  .health-bar-fill{{height:100%;border-radius:3px;}}
  .deploy-tag{{padding:4px 10px;border-radius:6px;font-size:0.75rem;font-weight:800;}}
  .tag-ok{{background:rgba(16,185,129,0.15);color:var(--success);}}.tag-fail{{background:rgba(239,68,68,0.15);color:var(--fail);}}
  .diff-item{{margin-bottom:12px;padding:12px;border-radius:12px;background:rgba(15,23,42,0.3);font-size:0.85rem;border-left:4px solid var(--primary);}}
  .toast{{position:fixed;bottom:32px;right:32px;background:var(--primary);color:#fff;padding:12px 24px;border-radius:12px;font-weight:600;display:none;z-index:1000;}}
</style>
</head><body>
<nav><div class="brand">REBUILD</div>
<div style="margin-left:24px;font-weight:600;font-size:0.9rem;color:var(--text-dim)">TIME MACHINE</div>
<a href="dashboard.html" class="btn" style="margin-left:auto;text-decoration:none;">📊 Dashboard</a>
</nav>
<div class="toolbar">
  <button class="btn" onclick="copyFmt('json')">📋 JSON</button>
  <button class="btn btn-primary" onclick="dlFmt('json')">💾 Export All</button>
</div>
<div class="content">
  <div class="dashboard-grid">
    <div class="glass-card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <h3 style="margin:0">Health Trend</h3><span style="font-size:0.8rem;color:var(--text-dim)">Last {len(results)} days</span>
    </div>{trend_svg}</div>
    <div class="glass-card"><h3 style="margin:0 0 20px 0">Evolution Log</h3>
    <div style="max-height:200px;overflow-y:auto;">{diff_section or '<div style="color:var(--text-dim);font-size:0.9rem">No significant changes.</div>'}</div></div>
  </div>
  <h2 style="font-size:1.8rem;font-weight:800;margin:0 0 24px 0;">Historical Walkthrough</h2>
  <div class="table-container"><table>
    <thead><tr><th>Day</th><th>Commit</th><th>Health</th><th>Endpoints</th><th>Deploy</th><th>Duration</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
</div>
<div id="toast" class="toast"></div>
<script>
const DATA={export_js};
function showToast(m){{const t=document.getElementById('toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',3000);}}
function copyFmt(f){{navigator.clipboard.writeText(JSON.stringify(DATA,null,2)).then(()=>showToast('Copied!'));}}
function dlFmt(f){{const b=new Blob([JSON.stringify(DATA,null,2)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='rebuild-history.json';a.click();}}
</script>
</body></html>"""
