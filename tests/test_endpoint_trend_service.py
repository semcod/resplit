"""Unit tests for ``rebuild.application.services.endpoint_trend_service``.

Locks down the dataclass shape and the three public adapters
(``compute_endpoint_count_trend``, ``..._dict``, ``..._labels``) so the
single-source-of-truth migration (Sprint 5b / 2026-05-08) cannot regress.
"""
from __future__ import annotations

from datetime import date

import pytest

from rebuild.application.services.endpoint_trend_service import (
    DEFAULT_ENDPOINT_WARNING_PCT,
    EndpointTrendPoint,
    compute_endpoint_count_trend,
    compute_endpoint_count_trend_dict,
    compute_endpoint_count_trend_labels,
)
from rebuild.domain.day_result import DayResult
from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from rebuild.domain.models import DeployMethod


def _ep(path: str = "/h") -> Endpoint:
    return Endpoint(method="GET", path=path, base_url="http://x")


def _day(day_value: date, n_endpoints: int) -> DayResult:
    ep = _ep()
    ok = EndpointResult(endpoint=ep, status=EndpointStatus.OK)
    return DayResult(
        day=day_value,
        commit=None,
        deploy_method=DeployMethod.NONE,
        deploy_success=True,
        endpoints=[ep] * n_endpoints,
        endpoint_results=[ok] * n_endpoints,
    )


class TestComputeEndpointCountTrend:
    def test_empty_input_returns_empty_list(self):
        assert compute_endpoint_count_trend([]) == []

    def test_single_day_has_no_predecessor(self):
        points = compute_endpoint_count_trend([_day(date(2025, 1, 1), 5)])
        assert len(points) == 1
        p = points[0]
        assert isinstance(p, EndpointTrendPoint)
        assert p.day == "2025-01-01"
        assert p.total == 5
        assert p.delta is None
        assert p.label == "—"
        assert p.is_warning is False

    def test_zero_change_labelled_zero(self):
        points = compute_endpoint_count_trend([
            _day(date(2025, 1, 1), 10),
            _day(date(2025, 1, 2), 10),
        ])
        assert points[1].delta == 0
        assert points[1].label == "0"
        assert points[1].is_warning is False

    def test_small_increase_below_threshold(self):
        # 10 → 11 is +10% which is NOT > 10.0 default threshold.
        points = compute_endpoint_count_trend([
            _day(date(2025, 1, 1), 10),
            _day(date(2025, 1, 2), 11),
        ])
        assert points[1].delta == 1
        assert points[1].is_warning is False
        assert points[1].label.startswith("+1 (+10.0%)")

    def test_large_decrease_flagged_warning(self):
        # 10 → 1 is -90%, must trigger the ⚠ marker.
        points = compute_endpoint_count_trend([
            _day(date(2025, 1, 1), 10),
            _day(date(2025, 1, 2), 1),
        ])
        assert points[1].delta == -9
        assert points[1].is_warning is True
        assert points[1].label.startswith("⚠")
        # The percent magnitude is unsigned; the *delta* keeps its sign.
        assert "-9 (90.0%)" in points[1].label

    def test_zero_previous_total_resets_baseline(self):
        # When previous_total == 0 we cannot compute a percentage; the day is
        # labelled "—" and the next-day baseline becomes its total.
        points = compute_endpoint_count_trend([
            _day(date(2025, 1, 1), 0),
            _day(date(2025, 1, 2), 5),
        ])
        assert points[0].label == "—"
        assert points[1].label == "—"  # still no usable baseline
        assert points[1].is_warning is False

    def test_input_order_independence(self):
        days = [
            _day(date(2025, 1, 3), 12),
            _day(date(2025, 1, 1), 10),
            _day(date(2025, 1, 2), 11),
        ]
        # Reverse-chronological input must yield chronological output.
        ordered = compute_endpoint_count_trend(days)
        assert [p.day for p in ordered] == ["2025-01-01", "2025-01-02", "2025-01-03"]

    def test_custom_threshold_changes_warning(self):
        days = [_day(date(2025, 1, 1), 10), _day(date(2025, 1, 2), 11)]
        loose = compute_endpoint_count_trend(days, warning_threshold_pct=15.0)
        strict = compute_endpoint_count_trend(days, warning_threshold_pct=5.0)
        assert loose[1].is_warning is False
        assert strict[1].is_warning is True

    def test_default_threshold_constant(self):
        assert DEFAULT_ENDPOINT_WARNING_PCT == 10.0


class TestAdapters:
    def test_dict_adapter_keys_by_iso_day(self):
        # 10 → 11 = +10% which is NOT > 10.0% threshold (we want a non-warning label).
        out = compute_endpoint_count_trend_dict([
            _day(date(2025, 1, 1), 10),
            _day(date(2025, 1, 2), 11),
        ])
        assert set(out.keys()) == {"2025-01-01", "2025-01-02"}
        assert out["2025-01-01"] == "—"
        assert out["2025-01-02"].startswith("+1")
        assert "⚠" not in out["2025-01-02"]

    def test_labels_adapter_returns_list(self):
        labels = compute_endpoint_count_trend_labels([
            _day(date(2025, 1, 1), 10),
            _day(date(2025, 1, 2), 1),
        ])
        assert labels[0] == "—"
        assert labels[1].startswith("⚠")

    def test_helpers_module_delegates_to_service(self):
        """``interfaces/commands/helpers.compute_endpoint_count_trend_labels``
        must produce identical output to the canonical service."""
        from rebuild.interfaces.commands.helpers import (
            compute_endpoint_count_trend_labels as helper_fn,
        )
        days = [
            _day(date(2025, 1, 1), 10),
            _day(date(2025, 1, 2), 11),
            _day(date(2025, 1, 3), 5),
        ]
        assert helper_fn(days) == compute_endpoint_count_trend_labels(days)

    def test_reporter_internal_delegates_to_service(self):
        """The legacy ``ReporterService._endpoint_count_trend_by_day`` shim must
        return the same dict as the canonical service."""
        from rebuild.application.services.reporter_service import ReporterService

        days = [
            _day(date(2025, 1, 1), 10),
            _day(date(2025, 1, 2), 12),
        ]
        svc = ReporterService()
        # Match reporter's internal contract: pre-sorted ascending input.
        assert svc._endpoint_count_trend_by_day(days) == compute_endpoint_count_trend_dict(days)


@pytest.mark.parametrize("totals,expected_labels", [
    ([5], ["—"]),
    ([5, 5], ["—", "0"]),
    ([10, 12], ["—", None]),  # second is non-warning, sign + value
])
def test_label_smoke(totals, expected_labels):
    days = [_day(date(2025, 1, i + 1), n) for i, n in enumerate(totals)]
    labels = compute_endpoint_count_trend_labels(days)
    for got, want in zip(labels, expected_labels):
        if want is not None:
            assert got == want
