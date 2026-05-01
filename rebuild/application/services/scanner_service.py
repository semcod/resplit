from __future__ import annotations
import ast
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

        # 3. Static FastAPI route scan (source-level fallback)
        static_routes = self._scan_via_fastapi_routes(repo)
        if static_routes:
            existing = {(e.method, e.path) for e in endpoints}
            for ep in static_routes:
                if (ep.method, ep.path) not in existing:
                    endpoints.append(ep)
                    existing.add((ep.method, ep.path))

        # 4. Fallback: docker-compose Traefik labels
        if not endpoints:
            endpoints.extend(self._scan_via_compose_labels(repo))

        # 5. Minimalny fallback: /api/health
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

    def _scan_via_fastapi_routes(self, repo: Path) -> List[Endpoint]:
        methods = {"get", "post", "put", "delete", "patch"}
        endpoints: List[Endpoint] = []
        seen = set()

        for py_file in repo.rglob("*.py"):
            if any(part in py_file.parts for part in (".git", ".venv", "venv", "__pycache__", "node_modules", "tests")):
                continue

            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue

            router_prefixes = self._collect_router_prefixes(tree)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                for decorator in node.decorator_list:
                    if not isinstance(decorator, ast.Call):
                        continue
                    if not isinstance(decorator.func, ast.Attribute):
                        continue

                    method_name = decorator.func.attr.lower()
                    if method_name not in methods:
                        continue

                    raw_path = self._extract_route_path(decorator)
                    if not raw_path or not raw_path.startswith("/"):
                        continue

                    router_name = decorator.func.value.id if isinstance(decorator.func.value, ast.Name) else None
                    prefix = router_prefixes.get(router_name, "") if router_name else ""
                    full_path = self._join_route_path(prefix, raw_path)

                    key = (method_name.upper(), full_path)
                    if key in seen:
                        continue
                    seen.add(key)

                    endpoints.append(
                        Endpoint(
                            method=method_name.upper(),
                            path=full_path,
                            base_url=self.config.base_url,
                            description=node.name,
                        )
                    )

        return endpoints

    def _collect_router_prefixes(self, tree: ast.AST) -> dict:
        prefixes = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if not isinstance(node.value, ast.Call):
                continue

            func = node.value.func
            func_name = None
            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                func_name = func.attr

            if func_name != "APIRouter":
                continue

            prefix = ""
            for kw in node.value.keywords:
                if kw.arg == "prefix" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    prefix = kw.value.value
                    break

            for target in node.targets:
                if isinstance(target, ast.Name):
                    prefixes[target.id] = prefix

        return prefixes

    def _extract_route_path(self, decorator: ast.Call) -> Optional[str]:
        if decorator.args:
            arg = decorator.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return arg.value

        for kw in decorator.keywords:
            if kw.arg == "path" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return kw.value.value

        return None

    def _join_route_path(self, prefix: str, route: str) -> str:
        prefix = (prefix or "").strip()
        route = route.strip()
        if not prefix:
            return route
        if not prefix.startswith("/"):
            prefix = "/" + prefix
        return prefix.rstrip("/") + route

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

    _PARAM_FALLBACKS: dict = {
        "id": "1",
        "pk": "1",
        "uuid": "00000000-0000-0000-0000-000000000001",
        "slug": "test",
        "name": "test",
        "table": "users",
        "model": "test",
        "version": "v1",
        "format": "json",
        "lang": "en",
        "locale": "en",
        "date": "2024-01-01",
        "year": "2024",
        "month": "01",
        "day": "01",
    }

    def _substitute_params(self, path_template: str, fixtures: dict) -> str:
        actual = path_template
        for param in re.findall(r"\{([^}]+)\}", path_template):
            value = fixtures.get(param) or self._PARAM_FALLBACKS.get(param.lower())
            if value is None:
                value = "1"
            actual = actual.replace(f"{{{param}}}", str(value))
        return actual

    def _parse_openapi(self, spec: dict, base_url: str) -> List[Endpoint]:
        endpoints = []
        paths = spec.get("paths", {})
        fixtures = self.config.test_fixtures
        
        for path_template, methods in paths.items():
            actual_path = self._substitute_params(path_template, fixtures)
            has_unresolved = "{" in actual_path
            
            for method, details in methods.items():
                if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    desc = details.get("summary", "")
                    resolved_body = self._resolve_test_body(method.upper(), actual_path, path_template)
                    ep = Endpoint(
                        method=method.upper(),
                        path=actual_path,
                        template_path=path_template if actual_path != path_template else None,
                        base_url=base_url,
                        description=desc,
                        body=resolved_body,
                    )
                    if has_unresolved:
                        ep.template_path = path_template
                    endpoints.append(ep)
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
