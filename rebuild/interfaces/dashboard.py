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
            capture_output=True, text=True, timeout=30,
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
<title>rebuild — dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 24px; background: #f8fafc; color: #1e293b; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 4px; }}
  .meta {{ color: #64748b; font-size: 0.9rem; margin-bottom: 24px; }}
  .chart-wrap {{ background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,.07); max-width: 1100px; }}
</style>
</head>
<body>
<h1>📊 rebuild — dashboard</h1>
<div class="meta">{total_days} dni &nbsp;·&nbsp; health% (lewa oś){"&nbsp;·&nbsp; Avg CC (prawa oś)" if has_cc else ""}</div>
<div class="chart-wrap">
  <canvas id="chart" height="80"></canvas>
</div>
<script>
const ctx = document.getElementById('chart');
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
        tension: 0.3,
        pointRadius: 4,
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
        min: 0, max: 100,
        title: {{ display: true, text: 'Health %' }},
      }},{cc_axis}
    }},
    plugins: {{
      legend: {{ position: 'top' }},
      tooltip: {{ callbacks: {{
        label: ctx => ctx.dataset.label + ': ' + (ctx.parsed.y ?? '—')
      }} }}
    }}
  }}
}});
</script>
</body>
</html>"""
