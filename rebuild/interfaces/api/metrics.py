"""
Prometheus metrics for rebuild API.

Exposes standard counters, gauges and histograms for observability.
Requires ``prometheus-client`` (included in the ``api`` extras group).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


def _require_prometheus():
    """Import prometheus_client or raise a helpful error."""
    try:
        import prometheus_client  # noqa: F401
        return prometheus_client
    except ImportError as exc:
        raise ImportError(
            "prometheus-client is required for /metrics. "
            "Install with: pip install 'rebuild[api]'"
        ) from exc


def setup_metrics(app: "FastAPI", registry=None) -> None:
    """
    Register Prometheus metrics middleware and /metrics endpoint on *app*.

    Metrics exposed:
      - rebuild_http_requests_total (counter) — by method, path, status
      - rebuild_http_request_duration_seconds (histogram) — by method, path
      - rebuild_walks_total (counter) — walk commands dispatched
      - rebuild_scan_cache_hits_total (counter)
      - rebuild_scan_cache_misses_total (counter)
      - rebuild_active_ws_connections (gauge)
    """
    prom = _require_prometheus()

    # Default to a *fresh* registry per FastAPI app instead of ``prom.REGISTRY``.
    # Sharing the global default would raise ``ValueError: Duplicated timeseries``
    # on every additional ``create_app()`` call (tests, multi-app embedding, etc.).
    # Callers who want the global default can pass ``registry=prometheus_client.REGISTRY``.
    reg = registry if registry is not None else prom.CollectorRegistry(auto_describe=True)

    REQUEST_COUNT = prom.Counter(
        "rebuild_http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
        registry=reg,
    )
    REQUEST_DURATION = prom.Histogram(
        "rebuild_http_request_duration_seconds",
        "HTTP request latency",
        ["method", "path"],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        registry=reg,
    )
    WALKS_TOTAL = prom.Counter(
        "rebuild_walks_total",
        "Walk commands dispatched",
        registry=reg,
    )
    CACHE_HITS = prom.Counter(
        "rebuild_scan_cache_hits_total",
        "Scanner cache hits",
        registry=reg,
    )
    CACHE_MISSES = prom.Counter(
        "rebuild_scan_cache_misses_total",
        "Scanner cache misses",
        registry=reg,
    )
    WS_CONNECTIONS = prom.Gauge(
        "rebuild_active_ws_connections",
        "Active WebSocket connections",
        registry=reg,
    )

    # Store references on app.state for external access (e.g. tests)
    app.state.prom_registry = reg
    app.state.prom_walks_total = WALKS_TOTAL
    app.state.prom_cache_hits = CACHE_HITS
    app.state.prom_cache_misses = CACHE_MISSES
    app.state.prom_ws_connections = WS_CONNECTIONS

    # ─── Middleware ────────────────────────────────────────────────────────────
    import time
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response

    class PrometheusMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if request.url.path == "/metrics":
                return await call_next(request)
            start = time.perf_counter()
            response: Response = await call_next(request)
            elapsed = time.perf_counter() - start
            path = request.url.path
            REQUEST_COUNT.labels(
                method=request.method, path=path, status=response.status_code
            ).inc()
            REQUEST_DURATION.labels(method=request.method, path=path).observe(elapsed)
            return response

    app.add_middleware(PrometheusMiddleware)

    # ─── /metrics endpoint ─────────────────────────────────────────────────────
    from starlette.responses import Response as StarletteResponse

    @app.get("/metrics", tags=["meta"], include_in_schema=False)
    async def prometheus_metrics():
        body = prom.generate_latest(reg)
        return StarletteResponse(
            content=body,
            media_type=prom.CONTENT_TYPE_LATEST,
        )
