"""
rebuild.application.services.regression_service — single source of truth for
health-regression detection across reporter, CLI helpers, and notifications.

Before consolidation (Sprint 2 / 2026-05-07) the same threshold-based regression
logic was duplicated in:
  - `application/services/reporting/reporter.py:_health_trend_by_day`
  - `interfaces/commands/helpers.py:compute_health_trend_labels`

Both now delegate to `compute_health_trend()` here. The notification side
(`notification_service.notify_health_regression`) is a downstream consumer that
formats and dispatches messages; it does *not* duplicate the detection logic.

See ANALYSIS.md §P1.3 for the rationale.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from ...domain.day_result import DayResult


# Default delta (in percentage points) below which a day is flagged as a
# health regression vs. the previous day.
DEFAULT_REGRESSION_THRESHOLD_PP: float = 20.0


@dataclass(frozen=True)
class HealthTrendPoint:
    """A single chronological point in a health-pct trend.

    Attributes
    ----------
    day:
        ISO date string (e.g. "2026-05-07"). Stable for use as a dict key.
    health_pct:
        Health percentage for this day, in 0..100.
    delta:
        Difference vs. previous day in percentage points, rounded to 1 decimal.
        ``None`` for the first chronological day (no predecessor).
    label:
        Human-readable trend marker:
          - ``"—"`` for the first day,
          - ``"⚠ -X.Ypp"`` if delta <= -threshold (regression),
          - ``"+X.Ypp"`` for positive delta,
          - ``"-X.Ypp"`` for non-regressing negative delta,
          - ``"0.0pp"`` for unchanged.
    is_regression:
        ``True`` iff ``delta is not None and delta <= -threshold``.
    """

    day: str
    health_pct: float
    delta: Optional[float]
    label: str
    is_regression: bool


def compute_health_trend(
    results: Iterable[DayResult],
    regression_threshold: float = DEFAULT_REGRESSION_THRESHOLD_PP,
) -> List[HealthTrendPoint]:
    """Compute the per-day health trend with regression flags.

    The input is sorted chronologically (ascending by ``day``) before processing,
    so callers may pass any iterable order. The first point always has
    ``delta=None``, ``label='—'`` and ``is_regression=False``.

    Parameters
    ----------
    results:
        Iterable of :class:`DayResult` to analyze. Empty input → empty output.
    regression_threshold:
        Minimum drop (in percentage points) to flag as a regression.
        Default: ``DEFAULT_REGRESSION_THRESHOLD_PP`` (20.0).

    Returns
    -------
    list[HealthTrendPoint]
        Chronologically ordered trend points, one per input day.
    """
    points: List[HealthTrendPoint] = []
    previous: Optional[float] = None

    for r in sorted(results, key=lambda x: x.day):
        day_key = str(r.day)
        if previous is None:
            points.append(HealthTrendPoint(
                day=day_key,
                health_pct=r.health_pct,
                delta=None,
                label="—",
                is_regression=False,
            ))
            previous = r.health_pct
            continue

        delta = round(r.health_pct - previous, 1)
        is_regression = delta <= -regression_threshold

        if is_regression:
            label = f"⚠ {delta:.1f}pp"
        elif delta > 0:
            label = f"+{delta:.1f}pp"
        elif delta < 0:
            label = f"{delta:.1f}pp"
        else:
            label = "0.0pp"

        points.append(HealthTrendPoint(
            day=day_key,
            health_pct=r.health_pct,
            delta=delta,
            label=label,
            is_regression=is_regression,
        ))
        previous = r.health_pct

    return points


def compute_health_trend_dict(
    results_asc: Iterable[DayResult],
    regression_threshold: float = DEFAULT_REGRESSION_THRESHOLD_PP,
) -> dict:
    """Adapter — return the trend as a ``{day_str: label}`` mapping.

    Used by the HTML reporter which keys its rendering by ISO date string.
    """
    return {p.day: p.label for p in compute_health_trend(results_asc, regression_threshold)}


def compute_health_trend_labels(
    results: Iterable[DayResult],
    regression_threshold: float = DEFAULT_REGRESSION_THRESHOLD_PP,
) -> List[str]:
    """Adapter — return labels in chronological order as a flat list.

    Used by the CLI summary table (``rich.table.Table``) which iterates
    ``zip(results, labels)``.
    """
    return [p.label for p in compute_health_trend(results, regression_threshold)]
