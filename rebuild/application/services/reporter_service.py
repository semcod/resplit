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

        rows = ""
        for r in result.endpoint_results:
            rt = f"{r.response_time_ms:.0f} ms" if r.response_time_ms is not None else "—"
            error_cat = self._classify_error(r)
            cat_badge = f'<span style="background:#64748b;color:#fff;padding:2px 6px;border-radius:4px;font-size:11px">{error_cat}</span>' if error_cat else ""
            rows += f"""
            <tr>
              <td><code>{r.endpoint.method}</code></td>
              <td><a href="{r.endpoint.url}" target="_blank">{r.endpoint.path}</a></td>
              <td>{self._status_badge(r.status)}</td>
              <td>{r.http_status or "—"}</td>
              <td>{rt}</td>
              <td>{cat_badge}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<title>rebuild — {result.day}</title>
<style>
  body {{ font-family: 'Inter', system-ui, sans-serif; margin: 0; background: #f8fafc; color: #1e293b; }}
  nav {{ background: #0f172a; color: #fff; padding: 12px 24px; display: flex; gap: 20px; align-items: center; border-bottom: 1px solid #1e293b; }}
  .toolbar {{ background: #fff; border-bottom: 1px solid #e2e8f0; padding: 12px 24px; display: flex; gap: 10px; }}
  .btn {{ padding: 6px 12px; border-radius: 6px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; }}
  .btn:hover {{ background: #f1f5f9; border-color: #94a3b8; }}
  .btn-primary {{ background: #6366f1; color: #fff; border: none; }}
  .btn-primary:hover {{ background: #4f46e5; }}
  .content {{ padding: 24px; max-width: 1200px; margin: 0 auto; }}
  .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 24px; }}
  .stat-card {{ background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
  .stat-val {{ font-size: 2rem; font-weight: 800; margin-bottom: 4px; }}
  .stat-label {{ color: #64748b; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; }}
  th {{ background: #f8fafc; padding: 12px; text-align: left; font-size: 12px; color: #64748b; border-bottom: 1px solid #e2e8f0; }}
  td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; }}
  .hidden-data {{ display: none; }}
  .deploy-error {{ background: #fff1f2; border: 1px solid #fecdd3; padding: 20px; border-radius: 12px; margin-bottom: 24px; }}
  .deploy-error h3 {{ color: #e11d48; margin-top: 0; font-size: 16px; }}
  .log-box {{ background: #1e293b; color: #cbd5e1; padding: 16px; border-radius: 8px; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 13px; overflow-x: auto; white-space: pre-wrap; margin-top: 12px; }}
</style>
{self._get_js_helpers()}
</head>
<body>
<nav>
  <strong style="color:#38bdf8">rebuild</strong>
  <a href="../index.html" style="color:#94a3b8;text-decoration:none">Timeline</a>
  <span style="color:#fff">{result.day}</span>
</nav>

<div class="toolbar">
  <span style="align-self:center;margin-right:10px;font-weight:600;font-size:13px">Eksportuj:</span>
  <button class="btn" onclick="copyToClipboard('json')">📋 JSON</button>
  <button class="btn" onclick="copyToClipboard('yaml')">📋 YAML</button>
  <button class="btn" onclick="copyToClipboard('toon')">📋 TOON</button>
  <button class="btn btn-primary" onclick="downloadFile('json', 'report_{result.day}.json')">💾 Pobierz JSON</button>
  <button class="btn btn-primary" onclick="downloadFile('toon', 'report_{result.day}.toon')">💾 Pobierz TOON</button>
</div>

<div class="content">
  <div class="stat-grid">
    <div class="stat-card">
       <div class="stat-val" style="color:#6366f1">{result.health_pct}%</div>
       <div class="stat-label">Health Score</div>
    </div>
    <div class="stat-card">
       <div class="stat-val" style="color:#22c55e">{result.ok_count}</div>
       <div class="stat-label">OK Endpoints</div>
    </div>
    <div class="stat-card">
       <div class="stat-val" style="color:#ef4444">{result.fail_count}</div>
       <div class="stat-label">Failed</div>
    </div>
    <div class="stat-card">
       <div class="stat-val">{result.duration_seconds:.2f}s</div>
       <div class="stat-label">Duration</div>
    </div>
  </div>

  {f'''
  <div class="deploy-error">
    <h3>❌ Deployment Failed</h3>
    <p style="font-size: 14px; color: #64748b;">The service failed to start or pass health check. Review the logs below:</p>
    <div class="log-box">{result.deploy_log or "No logs captured."}</div>
  </div>
  ''' if not result.deploy_success and not result.is_dry_run else ""}

  <table>
    <thead><tr><th>Method</th><th>Path</th><th>Status</th><th>HTTP</th><th>Time</th><th>Category</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>

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
            health_color = "#22c55e" if r.health_pct >= 80 else "#f97316" if r.health_pct >= 50 else "#ef4444"
            rows += f"""
            <tr>
              <td><a href="{rel}/report.html"><strong>{r.day}</strong></a></td>
              <td><code>{r.commit.sha[:8] if r.commit else '—'}</code></td>
              <td style="color:{health_color}"><strong>{r.health_pct}%</strong></td>
              <td>{r.ok_count} / {len(r.endpoints)}</td>
              <td>{"✓" if r.deploy_success else "✗"}</td>
              <td>{r.duration_seconds:.2f}s</td>
            </tr>"""

        export_js = json.dumps(export_data, ensure_ascii=False)

        html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<title>rebuild — timeline</title>
<style>
  body {{ font-family: 'Inter', system-ui, sans-serif; margin: 0; background: #f8fafc; }}
  nav {{ background: #0f172a; color: #fff; padding: 12px 24px; display: flex; gap: 20px; align-items: center; }}
  nav a {{ color: #94a3b8; text-decoration: none; font-size: 14px; }}
  nav a:hover {{ color: #fff; }}
  .toolbar {{ background: #fff; border-bottom: 1px solid #e2e8f0; padding: 12px 24px; display: flex; gap: 10px; }}
  .btn {{ padding: 6px 12px; border-radius: 6px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; }}
  .btn:hover {{ background: #f1f5f9; border-color: #94a3b8; }}
  .btn-primary {{ background: #6366f1; color: #fff; border: none; }}
  .btn-primary:hover {{ background: #4f46e5; }}
  .toast {{ display:none; position:fixed; bottom:24px; right:24px; background:#1e293b; color:#fff; padding:10px 18px; border-radius:8px; font-size:14px; z-index:999; }}
  .content {{ padding: 24px; max-width: 1200px; margin: 0 auto; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; }}
  th {{ background: #f8fafc; padding: 12px; text-align: left; font-size: 12px; color: #64748b; border-bottom: 1px solid #e2e8f0; }}
  td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; }}
  a {{ color: #6366f1; text-decoration: none; font-weight: 500; }}
</style>
{self._get_js_helpers()}
</head>
<body>
<nav>
  <strong style="color:#38bdf8">rebuild</strong>
  <span style="color:#fff;font-size:1rem;font-weight:600">&#128197; timeline ({len(results)} dni)</span>
  <a href="dashboard.html" style="margin-left:auto">&#9650; Dashboard</a>
</nav>
<div class="toolbar">
  <span style="align-self:center;margin-right:10px;font-weight:600;font-size:13px">Eksportuj:</span>
  <button class="btn" onclick="copyFmt('json')">&#128203; JSON</button>
  <button class="btn" onclick="copyFmt('yaml')">&#128203; YAML</button>
  <button class="btn" onclick="copyFmt('toon')">&#128203; TOON</button>
  <button class="btn btn-primary" onclick="dlFmt('json')">&#8595; Pobierz JSON</button>
  <button class="btn btn-primary" onclick="dlFmt('yaml')">&#8595; Pobierz YAML</button>
  <button class="btn btn-primary" onclick="dlFmt('toon')">&#8595; Pobierz TOON</button>
</div>
<div class="content">
  {trend_svg if trend_svg else ""}
  {diff_section if diff_section else ""}
  <table>
    <thead><tr><th>Dzień</th><th>Commit</th><th>Health</th><th>OK/Total</th><th>Deploy</th><th>Czas</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
<div class="toast" id="toast"></div>
<script>
const DATA = {export_js};
function toYaml(d) {{
  return d.map(r => Object.entries(r).map(([k,v]) => k === Object.keys(r)[0] ? `- ${{k}}: ${{v}}` : `  ${{k}}: ${{v}}`).join('\\n')).join('\\n');
}}
function toToon(d) {{
  return ['modules:', ...d.flatMap(r => [
    `  - name: walk_${{r.day}}`, `    type: day_result`,
    `    health_pct: ${{r.health_pct}}`, `    ok: ${{r.ok}}`,
    `    fail: ${{r.fail}}`, `    commit: ${{r.commit || 'null'}}`,
  ])].join('\\n');
}}
function getContent(fmt) {{
  if (fmt==='json') return JSON.stringify(DATA, null, 2);
  if (fmt==='yaml') return toYaml(DATA);
  if (fmt==='toon') return toToon(DATA);
}}
function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 2000);
}}
function copyFmt(fmt) {{
  navigator.clipboard.writeText(getContent(fmt)).then(() => showToast('Skopiowano ' + fmt.toUpperCase() + '!'));
}}
function dlFmt(fmt) {{
  const ext = fmt === 'toon' ? 'yaml' : fmt;
  const blob = new Blob([getContent(fmt)], {{type:'text/plain'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = `rebuild-history.${{ext}}`; a.click();
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
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin-bottom:16px;">
              <div style="font-weight:600;font-size:14px;margin-bottom:8px;">{prev.day} → {curr.day}</div>
              {f'<div style="color:#22c55e;font-size:13px;">+ {len(added)} added: {", ".join(sorted(added)[:3])}{"..." if len(added) > 3 else ""}</div>' if added else ""}
              {f'<div style="color:#ef4444;font-size:13px;">- {len(removed)} removed: {", ".join(sorted(removed)[:3])}{"..." if len(removed) > 3 else ""}</div>' if removed else ""}
            </div>"""
        if not diff_rows:
            return ""
        return f'<div style="margin:24px 0;"><h3 style="margin:0 0 12px 0;font-size:16px;">Endpoint Changes</h3>{diff_rows}</div>'
