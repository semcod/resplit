"""Per-day HTML report rendering.

Pure functions extracted from :class:`ReporterService` (Sprint 5b / 2026-05-08).
``render_day_html(result, data)`` produces the full HTML document; the small
helpers (`render_endpoint_rows`, `render_deploy_section`) are unit-testable in
isolation and reused by tests / future template engines.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from .formatters import classify_error, status_badge, to_toon, to_yaml
from ._html_assets import CSS_VARS, JS_HELPERS

if TYPE_CHECKING:
    from ....domain.day_result import DayResult
    from ....domain.endpoint import EndpointResult


def render_endpoint_row(endpoint_result: "EndpointResult") -> str:
    """Render a single ``<tr>`` for the per-day endpoint table."""
    r = endpoint_result
    rt = f"{r.response_time_ms:.0f}ms" if r.response_time_ms is not None else "—"
    error_cat = classify_error(r)
    cat_badge = f'<span class="badge badge-cat">{error_cat}</span>' if error_cat else ""
    template_html = (
        f'<div class="path-template">{r.endpoint.template_path}</div>'
        if r.endpoint.template_path and r.endpoint.template_path != r.endpoint.path
        else ""
    )
    code_class = str(r.http_status)[0] if r.http_status else "x"
    return (
        f'<tr class="endpoint-row">'
        f'<td><span class="method-tag method-{r.endpoint.method.lower()}">{r.endpoint.method}</span></td>'
        f'<td class="path-cell">'
        f'<div class="path-text" title="{r.endpoint.url}">{r.endpoint.path}</div>'
        f'{template_html}</td>'
        f'<td>{status_badge(r.status)}</td>'
        f'<td><span class="status-code code-{code_class}">{r.http_status or "—"}</span></td>'
        f'<td class="time-cell">{rt}</td>'
        f'<td>{cat_badge}</td>'
        f'</tr>'
    )


def render_endpoint_rows(result: "DayResult") -> str:
    """Render concatenated ``<tr>`` rows for ``result.endpoint_results``."""
    return "".join(render_endpoint_row(r) for r in result.endpoint_results)


def render_deploy_log(result: "DayResult") -> str:
    if result.deploy_success:
        return ""
    return f'<div class="log-box">{result.deploy_log or "No logs captured."}</div>'


def render_deploy_category(result: "DayResult") -> str:
    if not result.deploy_error_category:
        return ""
    return (
        f'<div style="margin-top:8px;color:var(--warn)">Category: '
        f'<strong>{result.deploy_error_category.value}</strong></div>'
    )


def render_deploy_section(result: "DayResult") -> str:
    """Render the deploy status block (or empty string for dry-run)."""
    if result.is_dry_run:
        return ""
    cls = "success" if result.deploy_success else "fail"
    title = "✓ Deployment Successful" if result.deploy_success else "✗ Deployment Failed"
    desc = (
        "Infrastructure started successfully."
        if result.deploy_success
        else "The service failed to reach healthy state. See logs below."
    )
    log_html = render_deploy_log(result)
    cat_html = render_deploy_category(result)
    return (
        f'<div class="deploy-status {cls}"><h3 style="margin-top:0">{title}</h3>'
        f'<p style="color:var(--text-dim)">{desc}</p>{cat_html}{log_html}</div>'
    )


def render_day_html(result: "DayResult", data: dict) -> str:
    """Render the full per-day ``report.html`` document."""
    json_data = json.dumps(data, indent=2)
    yaml_data = to_yaml(data)
    toon_data = to_toon(result)
    rows = render_endpoint_rows(result)
    deploy_section = render_deploy_section(result)
    commit_chip = (
        f'<span style="background:rgba(99,102,241,0.15);color:#a5b4fc;padding:4px 12px;'
        f'border-radius:20px;font-family:JetBrains Mono,monospace;font-size:0.85rem;">'
        f'{result.commit.sha[:8]} · {result.commit.message[:50]}</span>'
        if result.commit
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="pl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>rebuild — {result.day}</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{CSS_VARS}
  body{{font-family:'Outfit',sans-serif;margin:0;background:var(--bg);color:var(--text);min-height:100vh;}}
  nav{{background:rgba(15,23,42,0.8);backdrop-filter:blur(12px);padding:16px 32px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100;}}
  .brand{{font-weight:800;font-size:1.4rem;letter-spacing:-0.02em;}}
  .toolbar{{padding:16px 32px;display:flex;gap:12px;background:rgba(30,41,59,0.4);border-bottom:1px solid var(--border);}}
  .btn{{padding:8px 16px;border-radius:8px;border:1px solid var(--border);background:rgba(255,255,255,0.05);color:var(--text);cursor:pointer;font-size:13px;font-weight:600;}}
  .btn:hover{{background:rgba(255,255,255,0.1);}}
  .content{{padding:32px;max-width:1400px;margin:0 auto;}}
  .stat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:24px;margin-bottom:40px;}}
  .stat-card{{background:var(--card-bg);padding:24px;border-radius:20px;border:1px solid var(--border);}}
  .stat-val{{font-size:2.8rem;font-weight:800;line-height:1;margin-bottom:8px;}}
  .stat-label{{color:var(--text-dim);font-size:0.85rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;}}
  .deploy-status{{background:var(--card-bg);border-radius:20px;border:1px solid var(--border);padding:32px;margin-bottom:40px;}}
  .deploy-status.fail{{border-left:6px solid var(--fail);}}
  .deploy-status.success{{border-left:6px solid var(--success);}}
  .table-container{{background:var(--card-bg);border-radius:24px;border:1px solid var(--border);overflow:hidden;}}
  table{{width:100%;border-collapse:collapse;text-align:left;}}
  th{{padding:20px 24px;background:rgba(15,23,42,0.4);font-size:0.75rem;font-weight:700;text-transform:uppercase;color:var(--text-dim);letter-spacing:0.1em;border-bottom:1px solid var(--border);}}
  td{{padding:18px 24px;border-bottom:1px solid var(--border);font-size:0.95rem;}}
  .method-tag{{padding:4px 10px;border-radius:6px;font-size:0.75rem;font-weight:800;color:#fff;}}
  .method-get{{background:#10b981;}}.method-post{{background:#6366f1;}}.method-put{{background:#f59e0b;}}.method-delete{{background:#ef4444;}}
  .path-text{{font-weight:600;font-family:'JetBrains Mono',monospace;font-size:0.9rem;}}
  .path-template{{font-size:0.75rem;color:var(--text-dim);margin-top:4px;font-family:'JetBrains Mono',monospace;}}
  .status-code{{font-family:'JetBrains Mono',monospace;font-weight:700;padding:2px 8px;border-radius:4px;font-size:0.85rem;}}
  .code-2{{color:#10b981;background:rgba(16,185,129,0.1);}}.code-4{{color:#f59e0b;background:rgba(245,158,11,0.1);}}.code-5{{color:#ef4444;background:rgba(239,68,68,0.1);}}
  .badge{{padding:4px 10px;border-radius:12px;font-size:0.7rem;font-weight:700;text-transform:uppercase;}}
  .badge-cat{{background:rgba(148,163,184,0.15);color:#cbd5e1;}}
  .hidden-data{{display:none;}}
  .log-box{{background:#000;color:#10b981;padding:20px;border-radius:12px;font-family:'JetBrains Mono',monospace;font-size:0.85rem;overflow-x:auto;white-space:pre-wrap;margin-top:20px;max-height:400px;}}
</style>
{JS_HELPERS}
</head><body>
<nav><div class="brand">REBUILD</div>
<div style="display:flex;gap:24px;font-size:0.9rem">
  <a href="../index.html" style="color:var(--text-dim);text-decoration:none;">Timeline</a>
  <a href="../dashboard.html" style="color:var(--text-dim);text-decoration:none;">Dashboard</a>
</div></nav>
<div class="toolbar">
  <button class="btn" onclick="copyToClipboard('json')">📋 JSON</button>
  <button class="btn" onclick="copyToClipboard('yaml')">📋 YAML</button>
  <button class="btn" style="margin-left:auto" onclick="downloadFile('json','rebuild_{result.day}.json')">⬇ Download</button>
</div>
<div class="content">
  <div style="margin-bottom:40px"><div style="color:var(--primary);font-weight:700;margin-bottom:8px">DAILY ANALYSIS</div>
  <h1 style="font-size:2.5rem;font-weight:800;margin:0 0 8px 0;">{result.day}</h1>
  {commit_chip}
  </div>
  <div class="stat-grid">
    <div class="stat-card"><div class="stat-val" style="color:var(--primary)">{result.health_pct}%</div><div class="stat-label">Health Score</div></div>
    <div class="stat-card"><div class="stat-val" style="color:var(--success)">{result.ok_count}</div><div class="stat-label">Successes</div></div>
    <div class="stat-card"><div class="stat-val" style="color:var(--fail)">{result.fail_count}</div><div class="stat-label">Failures</div></div>
    <div class="stat-card"><div class="stat-val">{result.duration_seconds:.1f}s</div><div class="stat-label">Duration</div></div>
  </div>
  {deploy_section}
  <div class="table-container"><table>
    <thead><tr><th>Method</th><th>Path</th><th>Status</th><th>HTTP</th><th>Latency</th><th>Meta</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <div id="data-json" class="hidden-data">{json_data}</div>
  <div id="data-yaml" class="hidden-data">{yaml_data}</div>
  <div id="data-toon" class="hidden-data">{toon_data}</div>
</div></body></html>"""
