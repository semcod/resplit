"""
rebuild.dashboard — timeline CC (cyclomatic complexity) nałożony na health%.

Generuje .rebuild/dashboard.html z dwoma osiami:
  - oś Y lewa: health% (z results.json per dzień)
  - oś Y prawa: średnie CC (z toon / regres scan per dzień)

Dane CC pobierane przez:
  1. subprocess `toon <repo> --format json --date <day>` (jeśli dostępny)
  2. Fallback: statyczne CC = None (brak danych)
"""

from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Optional

from ..domain.day_result import DayResult


# ──────────────────────────────────────────────
# CC via toon
# ──────────────────────────────────────────────


def get_cc_for_day(repo: Path, day: date) -> Optional[float]:
    """
    Wywołuje `toon <repo> --format json` i zwraca średnie CC dla danego dnia.
    Zwraca None jeśli toon niedostępny lub brak danych.
    """
    try:
        result = subprocess.run(
            ["toon", str(repo), "--format", "json", "--date", str(day)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        return _extract_avg_cc(data)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def _extract_avg_cc(data: dict) -> Optional[float]:
    """Wyciąga średnie CC z wyniku toon JSON."""
    files = data.get("files", [])
    if not files:
        return None
    cc_values = [f.get("avg_complexity") for f in files if f.get("avg_complexity") is not None]
    if not cc_values:
        return None
    return round(sum(cc_values) / len(cc_values), 2)


# ──────────────────────────────────────────────
# Główny generator
# ──────────────────────────────────────────────


def generate_dashboard(
    results: list[DayResult],
    output_dir: Path,
    repo: Optional[Path] = None,
) -> Path:
    """
    Generuje dashboard.html w output_dir.

    Jeśli repo podane → próbuje pobrać CC per dzień przez toon.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    sorted_results = sorted(results, key=lambda r: r.day)
    days = [str(r.day) for r in sorted_results]
    health = [r.health_pct for r in sorted_results]

    cc_values: list[Optional[float]] = []
    for r in sorted_results:
        if repo:
            cc_values.append(get_cc_for_day(repo, r.day))
        else:
            cc_values.append(None)

    html = _render_html(days, health, cc_values, len(results))
    out_path = output_dir / "dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


# ──────────────────────────────────────────────
# HTML rendering (inline Chart.js via CDN)
# ──────────────────────────────────────────────


def _render_html(
    days: list[str],
    health: list[float],
    cc: list[Optional[float]],
    total_days: int,
) -> str:
    days_js = json.dumps(days)
    health_js = json.dumps(health)
    cc_js = json.dumps(cc)

    has_cc = any(v is not None for v in cc)
    cc_dataset = ""
    if has_cc:
        cc_dataset = f"""
        {{
          label: 'Avg CC',
          data: {cc_js},
          borderColor: '#f97316',
          backgroundColor: 'rgba(249,115,22,0.1)',
          yAxisID: 'y2',
          tension: 0.3,
          pointRadius: 3,
        }},"""

    cc_axis = ""
    if has_cc:
        cc_axis = """
        y2: {
          type: 'linear',
          display: true,
          position: 'right',
          title: { display: true, text: 'Avg CC' },
          grid: { drawOnChartArea: false },
        },"""

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>rebuild — dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
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
  }}
  body {{
    font-family: 'Outfit', sans-serif;
    margin: 0;
    background: var(--bg);
    background-image: radial-gradient(circle at 0% 100%, rgba(99, 102, 241, 0.1) 0%, transparent 50%);
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

  nav a {{ color: var(--text-dim); text-decoration: none; font-size: 0.9rem; margin-left: 24px; font-weight: 600; }}
  nav a:hover {{ color: var(--text); }}

  .content {{ padding: 32px; max-width: 1200px; margin: 0 auto; }}
  h1 {{ font-size: 2.2rem; font-weight: 800; margin: 0 0 8px 0; letter-spacing: -0.02em; }}
  .meta {{ color: var(--text-dim); font-size: 0.95rem; margin-bottom: 32px; }}

  .chart-container {{
    background: var(--card-bg);
    border-radius: 32px;
    border: 1px solid var(--border);
    padding: 32px;
    backdrop-filter: blur(12px);
    box-shadow: 0 20px 50px rgba(0,0,0,0.3);
  }}
  .hint {{ color: var(--text-dim); font-size: 0.85rem; margin-top: 16px; text-align: center; }}

  .logs-panel {{
    margin-top: 32px;
    background: var(--card-bg);
    border-radius: 24px;
    border: 1px solid var(--border);
    padding: 24px;
    backdrop-filter: blur(12px);
  }}
  .logs-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }}
  .logs-title {{ font-size: 1.2rem; font-weight: 700; }}
  .logs-status {{ font-size: 0.85rem; padding: 4px 12px; border-radius: 12px; background: rgba(16,185,129,0.2); color: #10b981; }}
  .logs-status.offline {{ background: rgba(239,68,68,0.2); color: #ef4444; }}
  .logs-container {{
    background: rgba(0,0,0,0.3);
    border-radius: 16px;
    padding: 16px;
    height: 200px;
    overflow-y: auto;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.85rem;
    border: 1px solid var(--border);
  }}
  .log-entry {{ margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
  .log-entry:last-child {{ border-bottom: none; }}
  .log-time {{ color: var(--text-dim); font-size: 0.75rem; }}
  .log-type {{ font-weight: 600; margin-left: 8px; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }}
  .log-type.pipeline {{ background: rgba(99,102,241,0.2); color: #6366f1; }}
  .log-type.deploy {{ background: rgba(249,115,22,0.2); color: #f97316; }}
  .log-type.test {{ background: rgba(16,185,129,0.2); color: #10b981; }}
  .log-type.error {{ background: rgba(239,68,68,0.2); color: #ef4444; }}
  .log-data {{ color: var(--text-dim); margin-left: 8px; }}
</style>
</head>
<body>
<nav>
  <div class="brand"><div class="brand-dot"></div> REBUILD</div>
  <a href="index.html">Timeline</a>
  <a href="#" style="color:var(--text)">Dashboard</a>
</nav>

<div class="content">
  <h1>Performance Analytics</h1>
  <div class="meta">{total_days} days analyzed &nbsp;·&nbsp; Health score & Complexity trend</div>

  <div class="chart-container">
    <canvas id="chart" height="100"></canvas>
    <div class="hint">💡 Pro-tip: Click on a data point to jump to that day's detailed report</div>
  </div>

  <div class="logs-panel">
    <div class="logs-header">
      <div class="logs-title">Live Event Stream</div>
      <div class="logs-status" id="logsStatus">Connecting...</div>
    </div>
    <div class="logs-container" id="logsContainer">
      <div class="log-entry"><span class="log-time">--:--:--</span><span class="log-type">INFO</span><span class="log-data">Waiting for events...</span></div>
    </div>
  </div>
</div>

<script>
const ctx = document.getElementById('chart');
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Outfit', sans-serif";

new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: {days_js},
    datasets: [
      {{
        label: 'Health %',
        data: {health_js},
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99,102,241,0.1)',
        yAxisID: 'y',
        tension: 0.4,
        pointRadius: 6,
        pointHoverRadius: 8,
        pointBackgroundColor: '#6366f1',
        fill: true,
      }},{cc_dataset}
    ]
  }},
  options: {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    scales: {{
      y: {{
        type: 'linear',
        display: true,
        position: 'left',
        min: 0, max: 105,
        grid: {{ color: 'rgba(255,255,255,0.05)' }},
        title: {{ display: true, text: 'Health %' }},
      }},{cc_axis}
    }},
    plugins: {{
      legend: {{ position: 'top', align: 'end' }},
      tooltip: {{
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        padding: 12,
        titleFont: {{ size: 14, weight: 'bold' }},
        bodyFont: {{ size: 13 }},
        cornerRadius: 8,
      }}
    }}
  }}
}});

ctx.addEventListener('click', function(e) {{
  const chart = Chart.getChart(ctx);
  const points = chart.getElementsAtEventForMode(e, 'nearest', {{ intersect: true }}, true);
  if (points.length) {{
    const day = {days_js}[points[0].index];
    window.location.href = day + '/report.html';
  }}
}});

// SSE Event Stream
const logsContainer = document.getElementById('logsContainer');
const logsStatus = document.getElementById('logsStatus');

function addLogEntry(event) {{
  const entry = document.createElement('div');
  entry.className = 'log-entry';

  const time = new Date(event.timestamp).toLocaleTimeString();
  const typeClass = event.type.includes('deploy') ? 'deploy' :
                    event.type.includes('test') ? 'test' :
                    event.type.includes('error') ? 'error' : 'pipeline';

  const dataStr = JSON.stringify(event.data).substring(0, 100);

  entry.innerHTML = `
    <span class="log-time">${{time}}</span>
    <span class="log-type ${{typeClass}}">${{event.type}}</span>
    <span class="log-data">${{dataStr}}</span>
  `;

  logsContainer.insertBefore(entry, logsContainer.firstChild);
  if (logsContainer.children.length > 50) {{
    logsContainer.removeChild(logsContainer.lastChild);
  }}
}}

function connectSSE() {{
  const evtSource = new EventSource('/events');

  evtSource.onopen = function() {{
    logsStatus.textContent = 'Live';
    logsStatus.classList.remove('offline');
  }};

  evtSource.onmessage = function(e) {{
    try {{
      const event = JSON.parse(e.data);
      addLogEntry(event);
    }} catch (err) {{
      console.error('Failed to parse event:', err);
    }}
  }};

  evtSource.onerror = function() {{
    logsStatus.textContent = 'Offline';
    logsStatus.classList.add('offline');
    evtSource.close();
    setTimeout(connectSSE, 5000);
  }};
}}

connectSSE();
</script>
</body>
</html>"""
