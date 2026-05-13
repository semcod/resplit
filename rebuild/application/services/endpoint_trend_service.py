"""
rebuild.application.services.endpoint_trend_service — single source of truth for
endpoint-count trend detection across the HTML reporter and CLI summary table.

Before consolidation (Sprint 5b / 2026-05-08) the same threshold-based delta
logic was duplicated in:
  - ``application/services/reporting/reporter.py:_endpoint_count_trend_by_day``
  - ``interfaces/commands/helpers.py:compute_endpoint_count_trend_labels``

Both now delegate to :func:`compute_endpoint_count_trend` here.

Mirrors :mod:`rebuild.application.services.regression_service` for the
analogous health-pct trend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from ...domain.day_result import DayResult


# Default delta (in % of previous-day endpoint count) above which a day is
# flagged as a notable change vs. the previous day.
DEFAULT_ENDPOINT_WARNING_PCT: float = 10.0


@dataclass(frozen=True)
class EndpointTrendPoint:
    """A single chronological point in an endpoint-count trend.

    Attributes
    ----------
    day:
        ISO date string (e.g. ``"2026-05-08"``). Stable for use as a dict key.
    total:
        Endpoint count for this day.
    delta:
        ``current_total - previous_total``. ``None`` for the first day.
    label:
        Human-readable trend marker:
          - ``"—"`` for the first day or when the previous total was 0,
          - ``"0"`` when delta == 0,
          - ``"⚠ +X (+Y.Z%)"`` / ``"⚠ -X (-Y.Z%)"`` if ``|pct| > warning_pct``,
          - ``"+X (+Y.Z%)"`` / ``"-X (-Y.Z%)"`` otherwise.
    is_warning:
        ``True`` iff the change exceeds ``warning_pct`` of the previous total.
    """

    day: str
    total: int
    delta: Optional[int]
    label: str
    is_warning: bool


def compute_endpoint_count_trend(
    results: Iterable[DayResult],
    warning_threshold_pct: float = DEFAULT_ENDPOINT_WARNING_PCT,
) -> List[EndpointTrendPoint]:
    """Compute the per-day endpoint-count trend with warning flags.

    Sorts the input chronologically (ascending by ``day``) before processing.
    Empty input → empty output.
    """
    points: List[EndpointTrendPoint] = []
    previous_total: Optional[int] = None

    for r in sorted(results, key=lambda x: x.day):
        day_key = str(r.day)
        current_total = len(r.endpoints)

        if previous_total is None or previous_total == 0:
            points.append(
                EndpointTrendPoint(
                    day=day_key,
                    total=current_total,
                    delta=None,
                    label="—",
                    is_warning=False,
                )
            )
            previous_total = current_total
            continue

        delta = current_total - previous_total
        if delta == 0:
            points.append(
                EndpointTrendPoint(
                    day=day_key,
                    total=current_total,
                    delta=0,
                    label="0",
                    is_warning=False,
                )
            )
            previous_total = current_total
            continue

        pct = abs(delta) / previous_total * 100.0
        sign = "+" if delta > 0 else ""
        base = f"{sign}{delta} ({sign}{pct:.1f}%)"
        is_warning = pct > warning_threshold_pct
        label = f"⚠ {base}" if is_warning else base

        points.append(
            EndpointTrendPoint(
                day=day_key,
                total=current_total,
                delta=delta,
                label=label,
                is_warning=is_warning,
            )
        )
        previous_total = current_total

    return points


def compute_endpoint_count_trend_dict(
    results_asc: Iterable[DayResult],
    warning_threshold_pct: float = DEFAULT_ENDPOINT_WARNING_PCT,
) -> dict:
    """Adapter — return the trend as a ``{day_str: label}`` mapping.

    Used by the HTML reporter which keys its rendering by ISO date string.
    """
    return {
        p.day: p.label for p in compute_endpoint_count_trend(results_asc, warning_threshold_pct)
    }


def compute_endpoint_count_trend_labels(
    results: Iterable[DayResult],
    warning_threshold_pct: float = DEFAULT_ENDPOINT_WARNING_PCT,
) -> List[str]:
    """Adapter — return labels in chronological order as a flat list.

    Used by the CLI summary table (``rich.table.Table``) which iterates
    ``zip(results, labels)``.
    """
    return [p.label for p in compute_endpoint_count_trend(results, warning_threshold_pct)]
