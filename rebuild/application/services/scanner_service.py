from __future__ import annotations
import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional

import httpx
import yaml

from ...domain.models import WalkConfig
from ...domain.endpoint import Endpoint
from .base import Service

class ScannerService(Service[Path, List[Endpoint]]):
    """
    Service for discovering API endpoints in a repository.
    """
    def __init__(self, config: WalkConfig):
        self.config = config

    def execute(self, repo: Path) -> List[Endpoint]:
        endpoints: List[Endpoint] = []

        # 1. deta scan
        deta_endpoints = self._scan_via_deta(repo)
        if deta_endpoints:
            endpoints.extend(deta_endpoints)

        # 2. OpenAPI
        openapi_endpoints = self._scan_via_openapi(self.config.base_url, repo)
        if openapi_endpoints:
            existing = {(e.method, e.path) for e in endpoints}
            for ep in openapi_endpoints:
                if (ep.method, ep.path) not in existing:
                    endpoints.append(ep)
                    existing.add((ep.method, ep.path))

        # 3. Fallback: docker-compose Traefik labels
        if not endpoints:
            endpoints.extend(self._scan_via_compose_labels(repo))

        # 4. Minimalny fallback: /api/health
        if not endpoints:
            endpoints.append(Endpoint(method="GET", path="/api/health", base_url=self.config.base_url))

        return endpoints

    def _scan_via_deta(self, repo: Path) -> List[Endpoint]:
        try:
            result = subprocess.run(
                ["deta", "scan", str(repo), "--formats", "json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return []
            data = json.loads(result.stdout)
            return self._ports_to_endpoints(data, self.config.base_url)
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return []

    def _ports_to_endpoints(self, data: dict, base_url: str) -> List[Endpoint]:
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

    def _scan_via_openapi(self, base_url: str, repo: Path) -> List[Endpoint]:
        # In dry-run and accelerator mode prefer static OpenAPI from repo/worktree.
        # This makes endpoint discovery reproducible per commit.
        prefer_static = self.config.dry_run or getattr(self.config, "accelerator", False)
        if prefer_static:
            static = self._scan_via_openapi_file(repo)
            if static:
                return static

        # Fallback: probe live URL when static OpenAPI is unavailable.
        for path in ("/openapi.json", "/docs/openapi.json", "/api/openapi.json"):
            try:
                r = httpx.get(f"{base_url.rstrip('/')}{path}", timeout=5)
                if r.status_code == 200:
                    return self._parse_openapi(r.json(), base_url)
            except Exception:
                continue
        return []

    def _scan_via_openapi_file(self, repo: Path) -> List[Endpoint]:
        candidates = [
            repo / "openapi.json",
            repo / "docs" / "openapi.json",
            repo / "backend" / "openapi.json",
            repo / "api" / "openapi.json",
            repo / "generated" / "openapi.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                try:
                    spec = json.loads(candidate.read_text())
                    return self._parse_openapi(spec, self.config.base_url)
                except Exception:
                    continue
        return []

    def _parse_openapi(self, spec: dict, base_url: str) -> List[Endpoint]:
        endpoints = []
        paths = spec.get("paths", {})
        fixtures = self.config.test_fixtures
        
        for path_template, methods in paths.items():
            # Substitute {params}
            actual_path = path_template
            params = re.findall(r"\{([^}]+)\}", path_template)
            for p in params:
                if p in fixtures:
                    actual_path = actual_path.replace(f"{{{p}}}", str(fixtures[p]))
            
            for method, details in methods.items():
                if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    desc = details.get("summary", "")
                    resolved_body = self._resolve_test_body(method.upper(), actual_path, path_template)
                    endpoints.append(Endpoint(
                        method=method.upper(),
                        path=actual_path,
                        template_path=path_template if actual_path != path_template else None,
                        base_url=base_url,
                        description=desc,
                        body=resolved_body,
                    ))
        return endpoints

    def _resolve_test_body(self, method: str, actual_path: str, template_path: str) -> Optional[dict]:
        bodies = getattr(self.config, "test_bodies", {}) or {}
        candidates = [
            f"{method} {actual_path}",
            f"{method} {template_path}",
            actual_path,
            template_path,
        ]
        for key in candidates:
            value = bodies.get(key)
            if isinstance(value, dict):
                return value
        return None

    def _scan_via_compose_labels(self, repo: Path) -> List[Endpoint]:
        _TRAEFIK_RULE = re.compile(r"PathPrefix\(`([^`]+)`\)")
        for fname in ("docker-compose.yml", "docker-compose.yaml", self.config.compose_file):
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
                            base_url=self.config.base_url,
                            service=svc_name,
                        ))
            return endpoints
        return []
