"""
rebuild.endpoint_scanner — wykrywa endpointy przez deta scan lub OpenAPI.

Hierarchia:
  1. deta scan → infra.toon.yaml → lista portów/usług
  2. OpenAPI /openapi.json lub /docs/openapi.json → pełna lista endpointów
  3. Fallback: znane ścieżki z docker-compose labels (Traefik rules)
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Optional

import httpx
import yaml

from .domain.models import WalkConfig
from .domain.endpoint import Endpoint


# ──────────────────────────────────────────────
# Główny wejściowy punkt
# ──────────────────────────────────────────────

def scan_endpoints(repo: Path, config: WalkConfig) -> list[Endpoint]:
    """Zwraca listę Endpoint wykrytych dla danego commitu/deployu."""
    endpoints: list[Endpoint] = []

    # 1. Próba przez deta
    deta_endpoints = _scan_via_deta(repo, config)
    if deta_endpoints:
        endpoints.extend(deta_endpoints)

    # 2. OpenAPI
    openapi_endpoints = _scan_via_openapi(config.base_url)
    if openapi_endpoints:
        # Deduplikuj względem deta
        existing = {(e.method, e.path) for e in endpoints}
        for ep in openapi_endpoints:
            if (ep.method, ep.path) not in existing:
                endpoints.append(ep)
                existing.add((ep.method, ep.path))

    # 3. Fallback: docker-compose Traefik labels
    if not endpoints:
        endpoints.extend(_scan_via_compose_labels(repo, config))

    # 4. Minimalny fallback: /api/health
    if not endpoints:
        endpoints.append(Endpoint(method="GET", path="/api/health", base_url=config.base_url))

    return endpoints


# ──────────────────────────────────────────────
# deta scan
# ──────────────────────────────────────────────

def _scan_via_deta(repo: Path, config: WalkConfig) -> list[Endpoint]:
    """Uruchamia `deta scan` i parsuje porty → bazowe URL-e."""
    try:
        result = subprocess.run(
            ["deta", "scan", str(repo), "--formats", "json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
        return _ports_to_endpoints(data, config.base_url)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


def _ports_to_endpoints(data: dict, base_url: str) -> list[Endpoint]:
    """Konwertuje wynik deta scan na listę endpointów (tylko health per usługa)."""
    endpoints = []
    services = data.get("services", [])
    for svc in services:
        name = svc.get("name", "unknown")
        ports = svc.get("ports", [])
        for port_info in ports:
            host_port = port_info.get("host_port")
            if host_port:
                url = f"http://localhost:{host_port}"
                for path in ("/api/health", "/health", "/"):
                    endpoints.append(Endpoint(
                        method="GET",
                        path=path,
                        base_url=url,
                        service=name,
                    ))
    return endpoints


# ──────────────────────────────────────────────
# OpenAPI
# ──────────────────────────────────────────────

def _scan_via_openapi(base_url: str) -> list[Endpoint]:
    """Pobiera /openapi.json i parsuje wszystkie ścieżki."""
    for path in ("/openapi.json", "/docs/openapi.json", "/api/openapi.json"):
        try:
            r = httpx.get(f"{base_url.rstrip('/')}{path}", timeout=5)
            if r.status_code == 200:
                return _parse_openapi(r.json(), base_url)
        except Exception:
            continue
    return []


def _parse_openapi(spec: dict, base_url: str) -> list[Endpoint]:
    endpoints = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                desc = details.get("summary", "")
                endpoints.append(Endpoint(
                    method=method.upper(),
                    path=path,
                    base_url=base_url,
                    description=desc,
                ))
    return endpoints


# ──────────────────────────────────────────────
# Traefik labels fallback
# ──────────────────────────────────────────────

_TRAEFIK_RULE = re.compile(r"PathPrefix\(`([^`]+)`\)")


def _scan_via_compose_labels(repo: Path, config: WalkConfig) -> list[Endpoint]:
    """Parsuje docker-compose labels i wyciąga PathPrefix → endpointy."""
    for fname in ("docker-compose.yml", "docker-compose.yaml", config.compose_file):
        cf = repo / fname
        if not cf.exists():
            continue
        try:
            data = yaml.safe_load(cf.read_text())
        except yaml.YAMLError:
            continue

        endpoints = []
        services = (data or {}).get("services", {})
        for svc_name, svc_def in services.items():
            labels = svc_def.get("labels", [])
            if isinstance(labels, dict):
                labels = list(labels.values())
            for label in labels:
                for match in _TRAEFIK_RULE.finditer(str(label)):
                    prefix = match.group(1)
                    endpoints.append(Endpoint(
                        method="GET",
                        path=prefix,
                        base_url=config.base_url,
                        service=svc_name,
                    ))
        return endpoints

    return []
