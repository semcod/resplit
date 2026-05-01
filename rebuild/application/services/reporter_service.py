from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from typing import List, Optional

from ...domain.day_result import DayResult
from ...domain.endpoint import EndpointResult, EndpointStatus
from .base import Service

class ReporterService(Service[DayResult, None]):
    """
    Service for generating HTML and JSON reports.
    """
    def execute(self, result: DayResult) -> None:
        self.save_day(result)

    def save_json(self, result: DayResult) -> None:
        out = result.output_dir
        if not out:
            return
        out.mkdir(parents=True, exist_ok=True)

        if result.commit:
            (out / "commit.txt").write_text(
                f"{result.commit.sha}\n{result.commit.message}\n{result.commit.author}\n{result.commit.timestamp.isoformat()}\n"
            )

        eps = [
            {"method": ep.method, "path": ep.path, "url": ep.url, "service": ep.service}
            for ep in result.endpoints
        ]
        (out / "endpoints.json").write_text(json.dumps(eps, indent=2, ensure_ascii=False))

        results = []
        for r in result.endpoint_results:
            results.append({
                "method": r.endpoint.method,
                "path": r.endpoint.path,
                "url": r.endpoint.url,
                "status": r.status.value,
                "http_status": r.http_status,
                "response_time_ms": r.response_time_ms,
                "screenshot": str(r.screenshot_path) if r.screenshot_path else None,
                "testql_passed": r.testql_passed,
                "error": r.error,
            })
        (out / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))

    def _status_badge(self, status: EndpointStatus) -> str:
        colors = {
            EndpointStatus.OK: ("#22c55e", "✓ OK"),
            EndpointStatus.FAIL: ("#ef4444", "✗ FAIL"),
            EndpointStatus.TIMEOUT: ("#f97316", "⏱ TIMEOUT"),
            EndpointStatus.SKIP: ("#94a3b8", "– SKIP"),
            EndpointStatus.UNKNOWN: ("#94a3b8", "? UNKNOWN"),
        }
        color, label = colors.get(status, ("#94a3b8", status.value))
        return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{label}</span>'

    def _screenshot_html(self, r: EndpointResult, day_dir: Path) -> str:
        if not r.screenshot_path or not r.screenshot_path.exists():
            return "<em style='color:#94a3b8'>no screenshot</em>"
        rel = r.screenshot_path.relative_to(day_dir)
        return f'<a href="{rel}" target="_blank"><img src="{rel}" style="max-width:320px;border:1px solid #e2e8f0;border-radius:6px" loading="lazy"></a>'

    def save_html(self, result: DayResult) -> None:
        out = result.output_dir
        if not out:
            return
        out.mkdir(parents=True, exist_ok=True)

        commit_info = ""
        if result.commit:
            commit_info = f"""
            <div class="commit-box">
              <strong>Commit:</strong> <code>{result.commit.sha[:12]}</code>
              &nbsp;·&nbsp; {result.commit.message}
              &nbsp;·&nbsp; <em>{result.commit.author}</em>
              &nbsp;·&nbsp; {result.commit.timestamp.strftime("%H:%M:%S")}
            </div>"""

        rows = ""
        for r in result.endpoint_results:
            rt = f"{r.response_time_ms:.0f} ms" if r.response_time_ms is not None else "—"
            screenshot = self._screenshot_html(r, out)
            rows += f"""
            <tr>
              <td><code>{r.endpoint.method}</code></td>
              <td><a href="{r.endpoint.url}" target="_blank">{r.endpoint.path}</a></td>
              <td>{self._status_badge(r.status)}</td>
              <td>{r.http_status or "—"}</td>
              <td>{rt}</td>
              <td>{screenshot}</td>
            </tr>"""

        health_color = "#22c55e" if result.health_pct >= 80 else "#f97316" if result.health_pct >= 50 else "#ef4444"
        deploy_badge = (
            '<span style="background:#22c55e;color:#fff;padding:2px 8px;border-radius:4px">deployed</span>'
            if result.deploy_success else
            '<span style="background:#ef4444;color:#fff;padding:2px 8px;border-radius:4px">deploy failed</span>'
        )

        html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<title>rebuild — {result.day}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 24px; background: #f8fafc; color: #1e293b; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 4px; }}
  .meta {{ color: #64748b; font-size: 0.9rem; margin-bottom: 16px; }}
  .commit-box {{ background: #f1f5f9; border-left: 4px solid #6366f1; padding: 10px 14px; border-radius: 4px; margin-bottom: 16px; font-size: 0.88rem; }}
  .summary {{ display: flex; gap: 24px; margin-bottom: 20px; }}
  .stat {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 20px; min-width: 100px; }}
  .stat-value {{ font-size: 1.8rem; font-weight: 700; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.07); }}
  th {{ background: #f1f5f9; text-align: left; padding: 10px 12px; font-size: 0.83rem; color: #64748b; }}
  td {{ padding: 10px 12px; border-top: 1px solid #f1f5f9; vertical-align: top; }}
  code {{ background: #f1f5f9; padding: 1px 5px; border-radius: 3px; font-size: 0.85rem; }}
</style>
</head>
<body>
<h1>📋 rebuild — {result.day}</h1>
<div class="meta">
  Deploy: {deploy_badge} &nbsp;·&nbsp;
  Endpointów: {len(result.endpoints)} &nbsp;·&nbsp;
  Czas: {result.duration_seconds:.1f}s
</div>
{commit_info}
<div class="summary">
  <div class="stat">
    <div class="stat-value" style="color:{health_color}">{result.health_pct}%</div>
    <div>health</div>
  </div>
  <div class="stat">
    <div class="stat-value" style="color:#22c55e">{result.ok_count}</div>
    <div>OK</div>
  </div>
  <div class="stat">
    <div class="stat-value" style="color:#ef4444">{result.fail_count}</div>
    <div>FAIL</div>
  </div>
  <div class="stat">
    <div class="stat-value">{len(result.endpoints)}</div>
    <div>endpoints</div>
  </div>
</div>
<table>
  <thead>
    <tr>
      <th>Method</th><th>Path</th><th>Status</th><th>HTTP</th><th>Time</th><th>Screenshot</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
</body>
</html>"""
        (out / "report.html").write_text(html, encoding="utf-8")

    def save_day(self, result: DayResult) -> None:
        self.save_json(result)
        self.save_html(result)

    def save_timeline_index(self, results: List[DayResult], output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        rows = ""
        for r in sorted(results, key=lambda x: x.day, reverse=True):
            day_dir = r.output_dir or (output_dir / str(r.day))
            rel = day_dir.relative_to(output_dir) if day_dir.is_relative_to(output_dir) else day_dir
            health_color = "#22c55e" if r.health_pct >= 80 else "#f97316" if r.health_pct >= 50 else "#ef4444"
            commit_short = r.commit.sha[:8] if r.commit else "—"
            rows += f"""
            <tr>
              <td><a href="{rel}/report.html"><strong>{r.day}</strong></a></td>
              <td><code>{commit_short}</code></td>
              <td style="color:{health_color}"><strong>{r.health_pct}%</strong></td>
              <td>{r.ok_count} / {len(r.endpoints)}</td>
              <td>{r.fail_count}</td>
              <td>{"✓" if r.deploy_success else "✗"}</td>
              <td>{r.duration_seconds:.1f}s</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<title>rebuild — timeline</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 24px; background: #f8fafc; }}
  h1 {{ font-size: 1.6rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.07); }}
  th {{ background: #f1f5f9; text-align: left; padding: 10px 12px; font-size: 0.83rem; color: #64748b; }}
  td {{ padding: 10px 12px; border-top: 1px solid #f1f5f9; }}
  a {{ color: #6366f1; text-decoration: none; }}
  code {{ background: #f1f5f9; padding: 1px 5px; border-radius: 3px; font-size: 0.85rem; }}
</style>
</head>
<body>
<h1>📅 rebuild — timeline ({len(results)} dni)</h1>
<table>
  <thead>
    <tr><th>Dzień</th><th>Commit</th><th>Health</th><th>OK/Total</th><th>FAIL</th><th>Deploy</th><th>Czas</th></tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
</body>
</html>"""
        (output_dir / "index.html").write_text(html, encoding="utf-8")
