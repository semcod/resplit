"""Tests for Prometheus /metrics endpoint (Sprint 5a).

Each test uses a fresh ``CollectorRegistry`` (passed via ``setup_metrics(app, registry=...)``
or ``create_app(metrics_registry=...)``) so collectors do not collide between tests
and we never need to monkey-patch ``prometheus_client`` internals.
"""
from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import pytest


@pytest.fixture
def fresh_registry():
    """Provide a clean prometheus CollectorRegistry per test."""
    try:
        import prometheus_client
    except ImportError:
        pytest.skip("prometheus-client not installed")
    return prometheus_client.CollectorRegistry(auto_describe=True)


@pytest.fixture
def metrics_module():
    """Import (or re-import) the metrics module — module-level state is harmless
    because each test passes its own registry."""
    return importlib.import_module("rebuild.interfaces.api.metrics")


class TestRequirePrometheus:
    def test_missing_prometheus_raises(self):
        with patch.dict(sys.modules, {"prometheus_client": None}):
            mod_name = "rebuild.interfaces.api.metrics"
            if mod_name in sys.modules:
                del sys.modules[mod_name]
            mod = importlib.import_module(mod_name)
            with pytest.raises(ImportError, match="prometheus-client"):
                mod._require_prometheus()
        # Re-import cleanly so subsequent tests see the real prometheus_client.
        if "rebuild.interfaces.api.metrics" in sys.modules:
            del sys.modules["rebuild.interfaces.api.metrics"]
        importlib.import_module("rebuild.interfaces.api.metrics")

    def test_present_prometheus_returns_module(self, metrics_module):
        try:
            import prometheus_client  # noqa: F401
        except ImportError:
            pytest.skip("prometheus-client not installed")
        prom = metrics_module._require_prometheus()
        assert hasattr(prom, "Counter")


class TestSetupMetrics:
    def test_setup_adds_metrics_route(self, fresh_registry, metrics_module):
        """setup_metrics should add a /metrics GET route to the app."""
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        app = FastAPI()
        metrics_module.setup_metrics(app, registry=fresh_registry)

        client = TestClient(app)
        resp = client.get("/metrics")
        assert resp.status_code == 200
        # Either the empty registry produced no series (text == "") or our metrics appear.
        assert resp.headers["content-type"].startswith("text/plain") or "rebuild_" in resp.text

    def test_metrics_endpoint_returns_prometheus_format(self, fresh_registry, metrics_module):
        """Full integration: /metrics returns prometheus text format with our metrics."""
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        app = FastAPI()

        @app.get("/ping")
        async def ping():
            return {"ok": True}

        metrics_module.setup_metrics(app, registry=fresh_registry)

        client = TestClient(app)
        # Trigger a request so the request counter has at least one sample.
        client.get("/ping")

        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "rebuild_http_requests_total" in resp.text
        assert "rebuild_http_request_duration_seconds" in resp.text

    def test_app_state_exposes_registry_and_metrics(self, fresh_registry, metrics_module):
        """setup_metrics stores registry + counter/gauge handles on app.state."""
        try:
            from fastapi import FastAPI
        except ImportError:
            pytest.skip("fastapi not installed")

        app = FastAPI()
        metrics_module.setup_metrics(app, registry=fresh_registry)

        assert app.state.prom_registry is fresh_registry
        assert hasattr(app.state, "prom_walks_total")
        assert hasattr(app.state, "prom_cache_hits")
        assert hasattr(app.state, "prom_cache_misses")
        assert hasattr(app.state, "prom_ws_connections")


class TestMetricsMiddleware:
    def test_middleware_increments_request_counter(self, fresh_registry, metrics_module):
        """Requests to non-/metrics paths should increment the counter."""
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        app = FastAPI()

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        metrics_module.setup_metrics(app, registry=fresh_registry)

        client = TestClient(app)
        client.get("/health")

        resp = client.get("/metrics")
        assert resp.status_code == 200
        body = resp.text
        assert "rebuild_http_requests_total" in body
        # The /health label set should be present (path="/health").
        assert 'path="/health"' in body

    def test_middleware_skips_metrics_path_itself(self, fresh_registry, metrics_module):
        """/metrics requests should NOT be recorded (avoid feedback loop)."""
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        app = FastAPI()
        metrics_module.setup_metrics(app, registry=fresh_registry)

        client = TestClient(app)
        # First /metrics scrape — counter should remain empty.
        client.get("/metrics")
        resp = client.get("/metrics")
        body = resp.text
        assert 'path="/metrics"' not in body


class TestAppIntegration:
    def test_create_app_includes_metrics(self, fresh_registry):
        """create_app(metrics_registry=...) should expose /metrics with our series."""
        try:
            from fastapi.testclient import TestClient
            import prometheus_client  # noqa: F401
        except ImportError:
            pytest.skip("fastapi or prometheus-client not installed")

        from rebuild.interfaces.api.app import create_app

        app = create_app(metrics_registry=fresh_registry)
        client = TestClient(app)
        # Make at least one request so a counter sample exists.
        client.get("/health")
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "rebuild_http" in resp.text

    def test_create_app_health_still_works(self, fresh_registry):
        """Health endpoint remains functional with metrics enabled."""
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi not installed")

        from rebuild.interfaces.api.app import create_app

        app = create_app(metrics_registry=fresh_registry)
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
