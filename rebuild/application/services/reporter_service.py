from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from typing import List, Optional, Dict, Any

from ...domain.day_result import DayResult
from ...domain.endpoint import EndpointResult, EndpointStatus
from .base import Service

class ReporterService(Service[DayResult, None]):
    """
    Service for generating HTML, JSON, YAML, and TOON reports.
    Supports interactive UI features (Copy/Download).
    """
    def execute(self, result: DayResult) -> None:
        self.save_day(result)

    def to_yaml(self, data: Dict[str, Any], indent: int = 0) -> str:
        """Simple YAML generator (avoiding external dependency for small files)."""
        lines = []
        space = "  " * indent
        for k, v in data.items():
            if isinstance(v, dict):
                lines.append(f"{space}{k}:")
                lines.append(self.to_yaml(v, indent + 1))
            elif isinstance(v, list):
                lines.append(f"{space}{k}:")
                for item in v:
                    if isinstance(item, dict):
                        lines.append(f"{space}-")
                        lines.append(self.to_yaml(item, indent + 1))
                    else:
                        lines.append(f"{space}- {item}")
            else:
                lines.append(f"{space}{k}: {v}")
        return "\n".join(lines)

    def to_toon(self, result: DayResult) -> str:
        """Custom TOON format (Key-Value + Results List)."""
        lines = [
            f"type: rebuild_report",
            f"day: {result.day}",
            f"health: {result.health_pct}%",
            f"stats: {result.ok_count}/{len(result.endpoints)}",
            f"deploy: {'success' if result.deploy_success else 'failed'}",
            f"mode: {'dry-run' if result.is_dry_run else 'live'}",
            "---"
        ]
        for r in result.endpoint_results:
            err = f" ({r.error})" if r.error else ""
            lines.append(f"{r.endpoint.method} {r.endpoint.path} [{r.status.value}] {r.http_status or ''}{err}")
        return "\n".join(lines)

    def save_day(self, result: DayResult) -> None:
        out = result.output_dir
        if not out: return
        out.mkdir(parents=True, exist_ok=True)
        
        data = result.to_dict()
        
        # Save files
        (out / "results.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
        (out / "results.yaml").write_text(self.to_yaml(data))
        (out / "results.toon").write_text(self.to_toon(result))
        
        self.save_html(result)

    def _get_js_helpers(self) -> str:
        return """
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
            a.href = url;
            a.download = filename;
            a.click();
            window.URL.revokeObjectURL(url);
        }
        </script>
        """

    def save_html(self, result: DayResult) -> None:
        out = result.output_dir
        if not out: return
        
        data = result.to_dict()
        json_data = json.dumps(data, indent=2)
        yaml_data = self.to_yaml(data)
        toon_data = self.to_toon(result)

        # Build endpoint rows with evolution indicators
        rows = ""
        for r in result.endpoint_results:
            rt = f"{r.response_time_ms:.0f}ms" if r.response_time_ms is not None else "—"
            error_cat = self._classify_error(r)
            cat_badge = f'<span class="badge badge-cat">{error_cat}</span>' if error_cat else ""
            
            # Evolution logic (placeholder for now, could be passed from pipeline)
            evo_badge = "" 
            
            rows += f"""
            <tr class="endpoint-row">
              <td><span class="method-tag method-{r.endpoint.method.lower()}">{r.endpoint.method}</span></td>
              <td class="path-cell">
                <div class="path-text" title="{r.endpoint.url}">{r.endpoint.path}</div>
                {f'<div class="path-template">{r.endpoint.template_path}</div>' if r.endpoint.template_path and r.endpoint.template_path != r.endpoint.path else ""}
              </td>
              <td>{self._status_badge(r.status)}</td>
              <td><span class="status-code code-{str(r.http_status)[0] if r.http_status else 'x'}">{r.http_status or "—"}</span></td>
              <td class="time-cell">{rt}</td>
              <td>{cat_badge}{evo_badge}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>rebuild — {result.day}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0f172a;
    --card-bg: rgba(30, 41, 59, 0.7);
    --border: rgba(255, 255, 255, 0.1);
    --text: #f8fafc;
    --text-dim: #94a3b8;
    --primary: #6366f1;
    --success: #10b981;
    --fail: #ef4444;
    --warn: #f59e0b;
  }}
  body {{ 
    font-family: 'Outfit', sans-serif; 
    margin: 0; 
    background: var(--bg); 
    background-image: radial-gradient(circle at 0% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
                      radial-gradient(circle at 100% 100%, rgba(244, 63, 94, 0.1) 0%, transparent 50%);
    color: var(--text); 
    min-height: 100vh;
  }}
  nav {{ 
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(12px);
    padding: 16px 32px; 
    display: flex; 
    justify-content: space-between;
    align-items: center; 
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .brand {{ font-weight: 800; font-size: 1.4rem; letter-spacing: -0.02em; display: flex; align-items: center; gap: 8px; }}
  .brand-dot {{ width: 8px; height: 8px; background: var(--primary); border-radius: 50%; box-shadow: 0 0 12px var(--primary); }}
  .nav-links {{ display: flex; gap: 24px; font-size: 0.9rem; font-weight: 500; }}
  .nav-links a {{ color: var(--text-dim); text-decoration: none; transition: color 0.2s; }}
  .nav-links a:hover {{ color: var(--text); }}
  
  .toolbar {{ 
    padding: 16px 32px; 
    display: flex; 
    gap: 12px; 
    background: rgba(30, 41, 59, 0.4);
    border-bottom: 1px solid var(--border);
  }}
  .btn {{ 
    padding: 8px 16px; 
    border-radius: 8px; 
    border: 1px solid var(--border); 
    background: rgba(255,255,255,0.05); 
    color: var(--text);
    cursor: pointer; 
    font-size: 13px; 
    font-weight: 600; 
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .btn:hover {{ background: rgba(255,255,255,0.1); transform: translateY(-1px); }}
  .btn-primary {{ background: var(--primary); border: none; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3); }}
  .btn-primary:hover {{ background: #4f46e5; box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4); }}

  .content {{ padding: 32px; max-width: 1400px; margin: 0 auto; }}
  
  .header-section {{ margin-bottom: 40px; }}
  .header-section h1 {{ font-size: 2.5rem; font-weight: 800; margin: 0 0 8px 0; letter-spacing: -0.03em; }}
  .commit-badge {{ 
    display: inline-flex; 
    align-items: center; 
    gap: 8px; 
    background: rgba(99, 102, 241, 0.15); 
    color: #a5b4fc;
    padding: 4px 12px; 
    border-radius: 20px; 
    font-size: 0.85rem; 
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
  }}

  .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; margin-bottom: 40px; }}
  .stat-card {{ 
    background: var(--card-bg); 
    padding: 24px; 
    border-radius: 20px; 
    border: 1px solid var(--border); 
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    backdrop-filter: blur(8px);
    transition: transform 0.3s;
  }}
  .stat-card:hover {{ transform: translateY(-4px); }}
  .stat-val {{ font-size: 2.8rem; font-weight: 800; line-height: 1; margin-bottom: 8px; }}
  .stat-label {{ color: var(--text-dim); font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
  
  .deploy-status {{ 
    background: var(--card-bg); 
    border-radius: 20px; 
    border: 1px solid var(--border);
    padding: 32px;
    margin-bottom: 40px;
  }}
  .deploy-status.fail {{ border-left: 6px solid var(--fail); }}
  .deploy-status.success {{ border-left: 6px solid var(--success); }}
  
  .table-container {{ 
    background: var(--card-bg); 
    border-radius: 24px; 
    border: 1px solid var(--border);
    overflow: hidden;
    backdrop-filter: blur(8px);
    box-shadow: 0 20px 50px rgba(0,0,0,0.2);
  }}
  table {{ width: 100%; border-collapse: collapse; text-align: left; }}
  th {{ 
    padding: 20px 24px; 
    background: rgba(15, 23, 42, 0.4); 
    font-size: 0.75rem; 
    font-weight: 700; 
    text-transform: uppercase; 
    color: var(--text-dim); 
    letter-spacing: 0.1em;
    border-bottom: 1px solid var(--border);
  }}
  td {{ padding: 18px 24px; border-bottom: 1px solid var(--border); font-size: 0.95rem; }}
  .endpoint-row {{ transition: background 0.2s; }}
  .endpoint-row:hover {{ background: rgba(255,255,255,0.03); }}
  
  .method-tag {{ 
    padding: 4px 10px; 
    border-radius: 6px; 
    font-size: 0.75rem; 
    font-weight: 800; 
    color: #fff;
  }}
  .method-get {{ background: #10b981; }}
  .method-post {{ background: #6366f1; }}
  .method-put {{ background: #f59e0b; }}
  .method-delete {{ background: #ef4444; }}
  
  .path-cell {{ max-width: 400px; }}
  .path-text {{ font-weight: 600; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .path-template {{ font-size: 0.75rem; color: var(--text-dim); margin-top: 4px; font-family: 'JetBrains Mono', monospace; }}
  
  .status-code {{ 
    font-family: 'JetBrains Mono', monospace; 
    font-weight: 700; 
    padding: 2px 8px; 
    border-radius: 4px;
    font-size: 0.85rem;
  }}
  .code-2 {{ color: #10b981; background: rgba(16, 185, 129, 0.1); }}
  .code-4 {{ color: #f59e0b; background: rgba(245, 158, 11, 0.1); }}
  .code-5 {{ color: #ef4444; background: rgba(239, 68, 68, 0.1); }}
  
  .badge {{ padding: 4px 10px; border-radius: 12px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }}
  .badge-cat {{ background: rgba(148, 163, 184, 0.15); color: #cbd5e1; }}
  
  .hidden-data {{ display: none; }}
  .log-box {{ 
    background: #000; 
    color: #10b981; 
    padding: 20px; 
    border-radius: 12px; 
    font-family: 'JetBrains Mono', monospace; 
    font-size: 0.85rem; 
    overflow-x: auto; 
    white-space: pre-wrap; 
    margin-top: 20px;
    border: 1px solid #1e293b;
    max-height: 400px;
  }}
  
  /* Animations */
  @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  .stat-card {{ animation: fadeIn 0.4s ease-out both; }}
  .stat-card:nth-child(2) {{ animation-delay: 0.1s; }}
  .stat-card:nth-child(3) {{ animation-delay: 0.2s; }}
  .stat-card:nth-child(4) {{ animation-delay: 0.3s; }}
</style>
{self._get_js_helpers()}
</head>
<body>
<nav>
  <div class="brand">
    <div class="brand-dot"></div>
    REBUILD
  </div>
  <div class="nav-links">
    <a href="../index.html">Timeline</a>
    <a href="../dashboard.html">Dashboard</a>
    <a href="#" class="active" style="color:var(--text)">Day Report</a>
  </div>
</nav>

<div class="toolbar">
  <button class="btn" onclick="copyToClipboard('json')"><span>&#128196;</span> JSON</button>
  <button class="btn" onclick="copyToClipboard('yaml')"><span>&#128196;</span> YAML</button>
  <button class="btn btn-primary" style="margin-left:auto" onclick="downloadFile('json', 'rebuild_{result.day}.json')"><span>&#11015;</span> Download Results</button>
</div>

<div class="content">
  <div class="header-section">
    <div style="color:var(--primary); font-weight:700; margin-bottom:8px">DAILY ANALYSIS</div>
    <h1>{result.day}</h1>
    {f'<div class="commit-badge"><span>&#128187;</span> {result.commit.sha[:8]} · {result.commit.message[:50]}</div>' if result.commit else ""}
  </div>

  <div class="stat-grid">
    <div class="stat-card">
       <div class="stat-val" style="color:var(--primary)">{result.health_pct}%</div>
       <div class="stat-label">Health Score</div>
    </div>
    <div class="stat-card">
       <div class="stat-val" style="color:var(--success)">{result.ok_count}</div>
       <div class="stat-label">Success Rate</div>
    </div>
    <div class="stat-card">
       <div class="stat-val" style="color:var(--fail)">{result.fail_count}</div>
       <div class="stat-label">Failures</div>
    </div>
    <div class="stat-card">
       <div class="stat-val">{result.duration_seconds:.1f}s</div>
       <div class="stat-label">Scan Duration</div>
    </div>
  </div>

  {f'''
  <div class="deploy-status {"success" if result.deploy_success else "fail"}">
    <h3 style="margin-top:0">{"✓ Deployment Successful" if result.deploy_success else "✗ Deployment Failed"}</h3>
    <p style="color:var(--text-dim); font-size:0.95rem">
      {"Infrastructure started successfully and passed initial health checks." if result.deploy_success 
       else "The service failed to reach healthy state. Review the logs captured during deployment below."}
    </p>
    {f'<div class="log-box">{result.deploy_log or "No logs captured."}</div>' if not result.deploy_success else ""}
  </div>
  ''' if not result.is_dry_run else ""}

  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th>Method</th>
          <th>Endpoint Path</th>
          <th>Status</th>
          <th>HTTP</th>
          <th>Latency</th>
          <th>Meta</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>

  <div id="data-json" class="hidden-data">{json_data}</div>
  <div id="data-yaml" class="hidden-data">{yaml_data}</div>
  <div id="data-toon" class="hidden-data">{toon_data}</div>
</div>
</body>
</html>"""
        (out / "report.html").write_text(html, encoding="utf-8")

    def _results_to_export_data(self, results: List[DayResult]) -> list:
        out = []
        for r in sorted(results, key=lambda x: x.day, reverse=True):
            out.append({
                "day": str(r.day),
                "commit": r.commit.sha if r.commit else None,
                "commit_message": r.commit.message if r.commit else None,
                "health_pct": r.health_pct,
                "ok": r.ok_count,
                "fail": r.fail_count,
                "total": len(r.endpoints),
                "deploy_success": r.deploy_success,
                "duration_seconds": r.duration_seconds,
            })
        return out

    def save_timeline_index(self, results: List[DayResult], output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)

        export_data = self._results_to_export_data(results)
        (output_dir / "history.json").write_text(
            json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Generate trend chart SVG
        trend_svg = self._generate_trend_chart(results)

        # Generate endpoint diff between consecutive days
        diff_section = self._generate_endpoint_diff(results)

        rows = ""
        for r in sorted(results, key=lambda x: x.day, reverse=True):
            day_dir = r.output_dir or (output_dir / str(r.day))
            rel = day_dir.relative_to(output_dir) if day_dir.is_relative_to(output_dir) else day_dir
            health_color = "var(--success)" if r.health_pct >= 80 else "var(--warn)" if r.health_pct >= 50 else "var(--fail)"
            rows += f"""
            <tr class="day-row">
              <td><a href="{rel}/report.html" class="day-link">{r.day}</a></td>
              <td><code class="commit-hash">{r.commit.sha[:8] if r.commit else '—'}</code></td>
              <td>
                <div class="health-bar-bg"><div class="health-bar-fill" style="width:{r.health_pct}%; background:{health_color}"></div></div>
                <span style="color:{health_color}; font-weight:700; font-size:0.85rem">{r.health_pct}%</span>
              </td>
              <td class="stats-cell">
                <span class="stat-ok">{r.ok_count}</span> / <span class="stat-total">{len(r.endpoints)}</span>
              </td>
              <td><span class="deploy-tag {"tag-ok" if r.deploy_success else "tag-fail"}">{"✓ OK" if r.deploy_success else "✗ FAIL"}</span></td>
              <td class="time-cell">{r.duration_seconds:.1f}s</td>
            </tr>"""

        export_js = json.dumps(export_data, ensure_ascii=False)

        html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>rebuild — timeline</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0f172a;
    --card-bg: rgba(30, 41, 59, 0.7);
    --border: rgba(255, 255, 255, 0.1);
    --text: #f8fafc;
    --text-dim: #94a3b8;
    --primary: #6366f1;
    --success: #10b981;
    --fail: #ef4444;
    --warn: #f59e0b;
  }}
  body {{ 
    font-family: 'Outfit', sans-serif; 
    margin: 0; 
    background: var(--bg); 
    background-image: radial-gradient(circle at 100% 0%, rgba(99, 102, 241, 0.1) 0%, transparent 40%);
    color: var(--text); 
    min-height: 100vh;
  }}
  nav {{ 
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(12px);
    padding: 16px 32px; 
    display: flex; 
    align-items: center; 
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 100;
  }}
  .brand {{ font-weight: 800; font-size: 1.4rem; letter-spacing: -0.02em; display: flex; align-items: center; gap: 8px; }}
  .brand-dot {{ width: 8px; height: 8px; background: var(--primary); border-radius: 50%; box-shadow: 0 0 12px var(--primary); }}
  
  .toolbar {{ padding: 16px 32px; display: flex; gap: 12px; background: rgba(30, 41, 59, 0.4); border-bottom: 1px solid var(--border); overflow-x: auto; }}
  .btn {{ padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border); background: rgba(255,255,255,0.05); color: var(--text); cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; white-space: nowrap; }}
  .btn:hover {{ background: rgba(255,255,255,0.1); }}
  .btn-primary {{ background: var(--primary); border: none; }}

  .content {{ padding: 32px; max-width: 1200px; margin: 0 auto; }}
  h2 {{ font-size: 1.8rem; font-weight: 800; margin: 0 0 24px 0; letter-spacing: -0.02em; }}
  
  .dashboard-grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 24px; margin-bottom: 40px; }}
  .glass-card {{ background: var(--card-bg); border-radius: 24px; border: 1px solid var(--border); padding: 24px; backdrop-filter: blur(8px); }}
  
  .table-container {{ background: var(--card-bg); border-radius: 24px; border: 1px solid var(--border); overflow: hidden; }}
  table {{ width: 100%; border-collapse: collapse; text-align: left; }}
  th {{ padding: 20px 24px; background: rgba(15, 23, 42, 0.4); font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-dim); letter-spacing: 0.1em; }}
  td {{ padding: 18px 24px; border-bottom: 1px solid var(--border); }}
  .day-row:hover {{ background: rgba(255,255,255,0.03); }}
  
  .day-link {{ color: var(--text); text-decoration: none; font-weight: 700; font-size: 1.05rem; }}
  .day-link:hover {{ color: var(--primary); }}
  
  .commit-hash {{ font-family: 'JetBrains Mono', monospace; color: var(--text-dim); font-size: 0.85rem; }}
  
  .health-bar-bg {{ width: 100px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; display: inline-block; margin-right: 8px; vertical-align: middle; }}
  .health-bar-fill {{ height: 100%; border-radius: 3px; transition: width 1s ease-out; }}
  
  .deploy-tag {{ padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 800; }}
  .tag-ok {{ background: rgba(16, 185, 129, 0.15); color: var(--success); }}
  .tag-fail {{ background: rgba(239, 68, 68, 0.15); color: var(--fail); }}
  
  .toast {{ position: fixed; bottom: 32px; right: 32px; background: var(--primary); color: #fff; padding: 12px 24px; border-radius: 12px; font-weight: 600; box-shadow: 0 10px 25px rgba(0,0,0,0.3); display: none; z-index: 1000; }}
  
  .diff-item {{ margin-bottom: 12px; padding: 12px; border-radius: 12px; background: rgba(15, 23, 42, 0.3); font-size: 0.85rem; border-left: 4px solid var(--primary); }}
</style>
{self._get_js_helpers()}
</head>
<body>
<nav>
  <div class="brand"><div class="brand-dot"></div> REBUILD</div>
  <div style="margin-left: 24px; font-weight: 600; font-size: 0.9rem; color: var(--text-dim)">TIME MACHINE</div>
  <a href="dashboard.html" class="btn" style="margin-left: auto; text-decoration: none;">📊 Advanced Dashboard</a>
</nav>

<div class="toolbar">
  <button class="btn" onclick="copyFmt('json')">📋 JSON</button>
  <button class="btn" onclick="copyFmt('yaml')">📋 YAML</button>
  <button class="btn" onclick="copyFmt('toon')">📋 TOON</button>
  <button class="btn btn-primary" onclick="dlFmt('json')">💾 Export All</button>
</div>

<div class="content">
  <div class="dashboard-grid">
    <div class="glass-card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px">
        <h3 style="margin:0">Health Trend</h3>
        <span style="font-size:0.8rem; color:var(--text-dim)">Last {len(results)} days</span>
      </div>
      {trend_svg}
    </div>
    <div class="glass-card">
      <h3 style="margin:0 0 20px 0">Evolution Log</h3>
      <div style="max-height: 200px; overflow-y: auto;">
        {diff_section or '<div style="color:var(--text-dim); font-size:0.9rem">No significant changes detected.</div>'}
      </div>
    </div>
  </div>

  <h2>Historical Walkthrough</h2>
  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th>Analysis Day</th>
          <th>Commit</th>
          <th>Health Status</th>
          <th>Endpoints</th>
          <th>Deployment</th>
          <th>Duration</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>

<div id="toast" class="toast"></div>

<script>
const DATA = {export_js};
function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 3000);
}}
function copyFmt(fmt) {{
  const content = fmt === 'json' ? JSON.stringify(DATA, null, 2) : "Exporting " + fmt + "...";
  navigator.clipboard.writeText(content).then(() => showToast('Copied ' + fmt.toUpperCase() + ' to clipboard!'));
}}
function dlFmt(fmt) {{
  const blob = new Blob([JSON.stringify(DATA, null, 2)], {{type:'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = `rebuild-history.json`; a.click();
}}
</script>
</body>
</html>"""
        (output_dir / "index.html").write_text(html, encoding="utf-8")

    def _status_badge(self, status: EndpointStatus) -> str:
        colors = {
            EndpointStatus.OK: ("#22c55e", "✓ OK"),
            EndpointStatus.FAIL: ("#ef4444", "✗ FAIL"),
            EndpointStatus.TIMEOUT: ("#f97316", "⏱ TIMEOUT"),
            EndpointStatus.SKIP: ("#94a3b8", "– SKIP"),
        }
        color, label = colors.get(status, ("#94a3b8", status.value))
        return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{label}</span>'

    def _classify_error(self, result: EndpointResult) -> str:
        """Classify error into category for grouping."""
        if result.status == EndpointStatus.OK or result.status == EndpointStatus.SKIP:
            return ""
        if not result.error:
            return "unknown"
        err_lower = result.error.lower()
        # Auth errors
        if any(k in err_lower for k in ["unauthorized", "401", "forbidden", "403", "auth", "token"]):
            return "auth"
        # Template/param errors
        if any(k in err_lower for k in ["not found", "404", "missing", "template", "param"]):
            return "template"
        # Timeout errors
        if "timeout" in err_lower:
            return "timeout"
        # Server errors
        if any(k in err_lower for k in ["500", "internal", "server error"]):
            return "server"
        # Network/connection errors
        if any(k in err_lower for k in ["connection", "network", "refused"]):
            return "network"
        return "other"

    def _generate_trend_chart(self, results: List[DayResult]) -> str:
        """Generate inline SVG chart showing health% trend over time."""
        if not results:
            return ""
        sorted_results = sorted(results, key=lambda x: x.day)
        width = 800
        height = 120
        padding = 30
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
        # Color gradient based on average health
        avg_health = sum(r.health_pct for r in sorted_results) / len(sorted_results)
        stroke_color = "#22c55e" if avg_health >= 80 else "#f97316" if avg_health >= 50 else "#ef4444"

        svg = f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="background:#f8fafc;border-radius:8px;margin:24px 0;">
  <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" stroke="#cbd5e1" stroke-width="1"/>
  <line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#cbd5e1" stroke-width="1"/>
  <text x="{padding-5}" y="{padding}" text-anchor="end" font-size="10" fill="#64748b">100%</text>
  <text x="{padding-5}" y="{height-padding}" text-anchor="end" font-size="10" fill="#64748b">0%</text>
  <polyline points="{polyline}" fill="none" stroke="{stroke_color}" stroke-width="2" stroke-linejoin="round"/>
  {"".join(f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="3" fill="{stroke_color}"/>' for p in points)}
</svg>"""
        return svg

    def _generate_endpoint_diff(self, results: List[DayResult]) -> str:
        """Generate HTML section showing endpoint additions/removals between consecutive days."""
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
            diff_rows += f"""
            <div class="diff-item">
              <div style="font-weight:700; color:var(--text); margin-bottom:4px;">{prev.day} → {curr.day}</div>
              {f'<div style="color:var(--success)">+ {len(added)} added: {", ".join(sorted(added)[:2])}{"..." if len(added) > 2 else ""}</div>' if added else ""}
              {f'<div style="color:var(--fail)">- {len(removed)} removed: {", ".join(sorted(removed)[:2])}{"..." if len(removed) > 2 else ""}</div>' if removed else ""}
            </div>"""
        if not diff_rows:
            return ""
        return f'<div style="margin:24px 0;"><h3 style="margin:0 0 12px 0;font-size:16px;">Endpoint Changes</h3>{diff_rows}</div>'
