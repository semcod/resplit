from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ....domain.day_result import DayResult
from ..base import Service
from .formatters import to_yaml, to_toon, status_badge, classify_error
from .chart_builder import generate_trend_chart, generate_endpoint_diff

_JS_HELPERS = """
<script>
function copyToClipboard(format) {
    const data = document.getElementById('data-' + format).textContent;
    navigator.clipboard.writeText(data).then(() => {
        alert('Copied ' + format.toUpperCase() + ' to clipboard!');
    });
}
function downloadFile(format, filename) {
    const data = document.getElementById('data-' + format).textContent;
    const blob = new Blob([data], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    window.URL.revokeObjectURL(url);
}
</script>
"""

_CSS_VARS = """
  :root {
    --bg: #0f172a; --card-bg: rgba(30,41,59,0.7); --border: rgba(255,255,255,0.1);
    --text: #f8fafc; --text-dim: #94a3b8; --primary: #6366f1;
    --success: #10b981; --fail: #ef4444; --warn: #f59e0b;
  }
"""


class ReporterService(Service[DayResult, None]):
    """
    Thin orchestrator: delegates to formatters, chart_builder, and saves files.
    """

    def execute(self, result: DayResult) -> None:
        self.save_day(result)

    def to_yaml(self, data, indent: int = 0) -> str:
        return to_yaml(data, indent)

    def to_toon(self, result: DayResult) -> str:
        return to_toon(result)

    def save_day(self, result: DayResult) -> None:
        out = result.output_dir
        if not out:
            return
        out.mkdir(parents=True, exist_ok=True)

        data = result.to_dict()
        (out / "results.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
        (out / "results.yaml").write_text(to_yaml(data))
        (out / "results.toon").write_text(to_toon(result))
        self._save_html_day(result, out, data)

    def _save_html_day(self, result: DayResult, out: Path, data: dict) -> None:
        json_data = json.dumps(data, indent=2)
        yaml_data = to_yaml(data)
        toon_data = to_toon(result)

        rows = ""
        for r in result.endpoint_results:
            rt = f"{r.response_time_ms:.0f}ms" if r.response_time_ms is not None else "—"
            error_cat = classify_error(r)
            cat_badge = f'<span class="badge badge-cat">{error_cat}</span>' if error_cat else ""
            rows += (
                f'<tr class="endpoint-row">'
                f'<td><span class="method-tag method-{r.endpoint.method.lower()}">{r.endpoint.method}</span></td>'
                f'<td class="path-cell">'
                f'<div class="path-text" title="{r.endpoint.url}">{r.endpoint.path}</div>'
                + (f'<div class="path-template">{r.endpoint.template_path}</div>'
                   if r.endpoint.template_path and r.endpoint.template_path != r.endpoint.path else "")
                + f'</td>'
                f'<td>{status_badge(r.status)}</td>'
                f'<td><span class="status-code code-{str(r.http_status)[0] if r.http_status else "x"}">'
                f'{r.http_status or "—"}</span></td>'
                f'<td class="time-cell">{rt}</td>'
                f'<td>{cat_badge}</td>'
                f'</tr>'
            )

        deploy_section = ""
        if not result.is_dry_run:
            cls = "success" if result.deploy_success else "fail"
            title = "✓ Deployment Successful" if result.deploy_success else "✗ Deployment Failed"
            desc = ("Infrastructure started successfully." if result.deploy_success
                    else "The service failed to reach healthy state. See logs below.")
            log_html = f'<div class="log-box">{result.deploy_log or "No logs captured."}</div>' if not result.deploy_success else ""
            cat_html = ""
            if result.deploy_error_category:
                cat_html = f'<div style="margin-top:8px;color:var(--warn)">Category: <strong>{result.deploy_error_category.value}</strong></div>'
            deploy_section = f'<div class="deploy-status {cls}"><h3 style="margin-top:0">{title}</h3><p style="color:var(--text-dim)">{desc}</p>{cat_html}{log_html}</div>'

        html = f"""<!DOCTYPE html>
<html lang="pl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>rebuild — {result.day}</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{_CSS_VARS}
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
{_JS_HELPERS}
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
  {f'<span style="background:rgba(99,102,241,0.15);color:#a5b4fc;padding:4px 12px;border-radius:20px;font-family:JetBrains Mono,monospace;font-size:0.85rem;">{result.commit.sha[:8]} · {result.commit.message[:50]}</span>' if result.commit else ""}
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
        (out / "report.html").write_text(html, encoding="utf-8")

    def save_timeline_index(self, results: List[DayResult], output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)

        export_data = self._results_to_export_data(results)
        (output_dir / "history.json").write_text(
            json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        trend_svg = generate_trend_chart(results)
        diff_section = generate_endpoint_diff(results)
        export_js = json.dumps(export_data, ensure_ascii=False)

        rows = ""
        for r in sorted(results, key=lambda x: x.day, reverse=True):
            day_dir = r.output_dir or (output_dir / str(r.day))
            rel = day_dir.relative_to(output_dir) if day_dir.is_relative_to(output_dir) else day_dir
            hc = "var(--success)" if r.health_pct >= 80 else "var(--warn)" if r.health_pct >= 50 else "var(--fail)"
            dep_cls = "tag-ok" if r.deploy_success else "tag-fail"
            dep_txt = "✓ OK" if r.deploy_success else "✗ FAIL"
            cat_txt = f' <span style="color:var(--text-dim);font-size:0.75rem">({r.deploy_error_category.value})</span>' if r.deploy_error_category and not r.deploy_success else ""
            rows += (
                f'<tr class="day-row">'
                f'<td><a href="{rel}/report.html" class="day-link">{r.day}</a></td>'
                f'<td><code class="commit-hash">{r.commit.sha[:8] if r.commit else "—"}</code></td>'
                f'<td><div class="health-bar-bg"><div class="health-bar-fill" style="width:{r.health_pct}%;background:{hc}"></div></div>'
                f'<span style="color:{hc};font-weight:700;font-size:0.85rem">{r.health_pct}%</span></td>'
                f'<td><span class="stat-ok">{r.ok_count}</span> / <span class="stat-total">{len(r.endpoints)}</span></td>'
                f'<td><span class="deploy-tag {dep_cls}">{dep_txt}</span>{cat_txt}</td>'
                f'<td>{r.duration_seconds:.1f}s</td>'
                f'</tr>'
            )

        html = f"""<!DOCTYPE html>
<html lang="pl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>rebuild — timeline</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{_CSS_VARS}
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
        (output_dir / "index.html").write_text(html, encoding="utf-8")

    def _results_to_export_data(self, results: List[DayResult]) -> list:
        return [
            {
                "day": str(r.day),
                "commit": r.commit.sha if r.commit else None,
                "commit_message": r.commit.message if r.commit else None,
                "health_pct": r.health_pct,
                "ok": r.ok_count,
                "fail": r.fail_count,
                "total": len(r.endpoints),
                "deploy_success": r.deploy_success,
                "deploy_error_category": r.deploy_error_category.value if r.deploy_error_category else None,
                "duration_seconds": r.duration_seconds,
            }
            for r in sorted(results, key=lambda x: x.day, reverse=True)
        ]
