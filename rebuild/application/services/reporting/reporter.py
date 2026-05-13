"""Slim orchestrator that wires the per-day, timeline, and summary writers
into a single :class:`ReporterService` facade.

Refactored in Sprint 5b (2026-05-08). The previous 434-LOC monolith has been
split into focused, individually-testable modules:

* :mod:`._html_assets` – shared CSS / JS snippets
* :mod:`.day_html` – per-day ``report.html`` rendering
* :mod:`.timeline_html` – cross-day ``index.html`` + JSON export shape
* :mod:`.summary_export` – ``summary.csv`` and ``summary.md`` writers
* :mod:`.formatters` – YAML / TOON / status-badge / error-classifier helpers
* :mod:`.chart_builder` – SVG trend chart and endpoint-diff section

Trend logic (health regression + endpoint-count delta) lives in the canonical
``application/services/{regression,endpoint_trend}_service`` modules — never
duplicated here.

The public API of :class:`ReporterService` (``execute``, ``save_day``,
``save_timeline_index``, ``export_csv``, ``export_markdown``, ``to_yaml``,
``to_toon``) is preserved unchanged for backward compatibility.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ....domain.day_result import DayResult
from ..base import Service
from .day_html import (
    render_day_html,
    render_deploy_section,
    render_endpoint_row,
    render_endpoint_rows,
)
from .formatters import to_toon, to_yaml
from .summary_export import write_csv, write_markdown
from .timeline_html import build_export_data, render_timeline_html


class ReporterService(Service[DayResult, None]):
    """Thin facade orchestrating the per-day / timeline / summary writers."""

    # ─── Service interface ────────────────────────────────────────────────────

    def execute(self, result: DayResult) -> None:
        self.save_day(result)

    # ─── Format helpers (delegators kept for backward-compat) ────────────────

    def to_yaml(self, data, indent: int = 0) -> str:
        return to_yaml(data, indent)

    def to_toon(self, result: DayResult) -> str:
        return to_toon(result)

    # ─── Per-day writer ───────────────────────────────────────────────────────

    def save_day(self, result: DayResult) -> None:
        out = result.output_dir
        if not out:
            return
        out.mkdir(parents=True, exist_ok=True)

        data = result.to_dict()
        (out / "results.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
        (out / "results.yaml").write_text(to_yaml(data))
        (out / "results.toon").write_text(to_toon(result))
        (out / "report.html").write_text(render_day_html(result, data), encoding="utf-8")

    # ─── Timeline / index writer ──────────────────────────────────────────────

    def save_timeline_index(self, results: List[DayResult], output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)

        export_data = build_export_data(results)
        (output_dir / "history.json").write_text(
            json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (output_dir / "index.html").write_text(
            render_timeline_html(results, output_dir), encoding="utf-8"
        )

    # ─── Summary exporters ────────────────────────────────────────────────────

    def export_csv(self, results: List[DayResult], output_dir: Path) -> Path:
        return write_csv(results, output_dir)

    def export_markdown(self, results: List[DayResult], output_dir: Path) -> Path:
        return write_markdown(results, output_dir)

    # ─── Internal helpers (kept for backward-compatibility with tests / subclasses) ──
    #
    # These names were public-ish (single-underscore) on the previous implementation;
    # we keep them as thin delegators so subclasses or rare external callers do not
    # break. Prefer the module-level functions in ``day_html`` / ``timeline_html``
    # for new code.

    def _save_html_day(self, result: DayResult, out: Path, data: dict) -> None:
        (out / "report.html").write_text(render_day_html(result, data), encoding="utf-8")

    def _endpoint_rows(self, result: DayResult) -> str:
        return render_endpoint_rows(result)

    def _endpoint_row(self, endpoint_result) -> str:
        return render_endpoint_row(endpoint_result)

    def _deploy_section(self, result: DayResult) -> str:
        return render_deploy_section(result)

    def _health_trend_by_day(
        self, results_asc: List[DayResult], regression_threshold: float = 20.0
    ) -> dict:
        from ..regression_service import compute_health_trend_dict

        return compute_health_trend_dict(results_asc, regression_threshold)

    def _endpoint_count_trend_by_day(
        self, results_asc: List[DayResult], warning_threshold_pct: float = 10.0
    ) -> dict:
        from ..endpoint_trend_service import compute_endpoint_count_trend_dict

        return compute_endpoint_count_trend_dict(results_asc, warning_threshold_pct)

    def _results_to_export_data(self, results: List[DayResult]) -> list:
        return build_export_data(results)
