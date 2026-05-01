"""
resplit.tester — uruchamia testql scenarios per endpoint.

Hierarchia:
  1. Jeśli testql dostępny i scenarios_dir istnieje → uruchom testql
  2. Fallback → prosty HTTP GET probe (zachowanie z cli.py)

Wyniki zapisywane do:
  .resplit/YYYY-MM-DD/testql-results.json
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Optional

import httpx

from .models import Endpoint, EndpointResult, EndpointStatus, WalkConfig


# ──────────────────────────────────────────────
# Główny entry point
# ──────────────────────────────────────────────

def run_tests(
    endpoints: list[Endpoint],
    config: WalkConfig,
    day_dir: Path,
) -> list[EndpointResult]:
    """
    Testuje listę endpointów.

    Jeśli testql dostępny i scenarios_dir skonfigurowany → używa testql.
    W przeciwnym razie → HTTP probe per endpoint.
    """
    if config.testql_dir and config.testql_dir.exists() and _testql_available():
        return _run_via_testql(endpoints, config, day_dir)
    return _run_http_probe(endpoints, config)


# ──────────────────────────────────────────────
# testql runner
# ──────────────────────────────────────────────

def _testql_available() -> bool:
    """Sprawdza czy testql jest zainstalowany."""
    try:
        result = subprocess.run(
            ["testql", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_via_testql(
    endpoints: list[Endpoint],
    config: WalkConfig,
    day_dir: Path,
) -> list[EndpointResult]:
    """
    Uruchamia testql dla każdego pliku scenariusza w testql_dir.
    Parsuje wyniki i mapuje na EndpointResult.
    """
    results_path = day_dir / "testql-results.json"
    day_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "testql",
        str(config.testql_dir),
        "--url", config.base_url,
        "--output", str(results_path),
        "--format", "json",
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=config.repo_path,
        )
    except subprocess.TimeoutExpired:
        return _fallback_all_timeout(endpoints)
    except FileNotFoundError:
        return _run_http_probe(endpoints, config)

    if proc.returncode != 0 or not results_path.exists():
        return _run_http_probe(endpoints, config)

    return _parse_testql_results(results_path, endpoints, config)


def _parse_testql_results(
    results_path: Path,
    endpoints: list[Endpoint],
    config: WalkConfig,
) -> list[EndpointResult]:
    """
    Parsuje JSON z testql i mapuje na EndpointResult.

    Format testql JSON (zakładany):
    [
      {"path": "/api/health", "method": "GET", "passed": true,
       "http_status": 200, "response_time_ms": 45.2, "error": null},
      ...
    ]
    """
    try:
        raw = json.loads(results_path.read_text())
    except (json.JSONDecodeError, OSError):
        return _run_http_probe(endpoints, config)

    # Indeks wyników po (method, path)
    idx: dict[tuple[str, str], dict] = {}
    for item in raw:
        key = (item.get("method", "GET").upper(), item.get("path", ""))
        idx[key] = item

    ep_results: list[EndpointResult] = []
    for ep in endpoints:
        key = (ep.method, ep.path)
        item = idx.get(key)
        if item is None:
            ep_results.append(EndpointResult(endpoint=ep, status=EndpointStatus.UNKNOWN))
            continue

        passed = item.get("passed", False)
        status = EndpointStatus.OK if passed else EndpointStatus.FAIL
        ep_results.append(EndpointResult(
            endpoint=ep,
            status=status,
            http_status=item.get("http_status"),
            response_time_ms=item.get("response_time_ms"),
            testql_passed=passed,
            error=item.get("error"),
        ))

    return ep_results


# ──────────────────────────────────────────────
# HTTP probe fallback
# ──────────────────────────────────────────────

def _run_http_probe(
    endpoints: list[Endpoint],
    config: WalkConfig,
) -> list[EndpointResult]:
    """Prosty HTTP GET probe dla każdego endpointu GET."""
    results: list[EndpointResult] = []

    for ep in endpoints:
        if ep.method != "GET":
            results.append(EndpointResult(endpoint=ep, status=EndpointStatus.SKIP))
            continue

        t0 = time.time()
        try:
            r = httpx.get(ep.url, timeout=8, follow_redirects=True)
            ms = (time.time() - t0) * 1000
            status = EndpointStatus.OK if r.status_code < 400 else EndpointStatus.FAIL
            results.append(EndpointResult(
                endpoint=ep,
                status=status,
                http_status=r.status_code,
                response_time_ms=ms,
            ))
        except httpx.TimeoutException:
            results.append(EndpointResult(endpoint=ep, status=EndpointStatus.TIMEOUT))
        except Exception as exc:
            results.append(EndpointResult(
                endpoint=ep,
                status=EndpointStatus.FAIL,
                error=str(exc),
            ))

    return results


def _fallback_all_timeout(endpoints: list[Endpoint]) -> list[EndpointResult]:
    return [EndpointResult(endpoint=ep, status=EndpointStatus.TIMEOUT) for ep in endpoints]
