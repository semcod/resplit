"""
Parallel test execution with dependency graph and health-first strategy.
"""
from __future__ import annotations
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

import httpx

from ...domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from ...domain.models import WalkConfig


@dataclass
class EndpointDependency:
    """Defines endpoint dependency relationship."""
    endpoint: str  # Path like /api/users
    depends_on: List[str]  # Paths it depends on
    is_critical: bool = False  # If this fails, skip dependents


class EndpointDependencyGraph:
    """
    Builds and manages endpoint dependency graph.
    
    Example:
        /health → no deps, run first
        /auth/login → no deps, can parallel
        /user/profile → depends on /auth/login
        /dashboard → depends on /user/profile
    """
    
    def __init__(self):
        self._deps: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_deps: Dict[str, Set[str]] = defaultdict(set)
        self._critical: Set[str] = set()
        self._groups: Dict[str, str] = {}
    
    def add_dependency(self, endpoint: str, depends_on: List[str], is_critical: bool = False):
        """Register endpoint dependency."""
        for dep in depends_on:
            self._deps[endpoint].add(dep)
            self._reverse_deps[dep].add(endpoint)
        
        if is_critical:
            self._critical.add(endpoint)
    
    def add_group(self, endpoint_pattern: str, group_name: str):
        """Assign endpoint to a test group."""
        self._groups[endpoint_pattern] = group_name
    
    def get_execution_order(self, endpoints: List[Endpoint]) -> List[List[Endpoint]]:
        """
        Group endpoints into execution phases.
        Each phase can run in parallel, phases run sequentially.
        """
        endpoint_map = {ep.path: ep for ep in endpoints}
        remaining = set(ep.path for ep in endpoints)
        phases: List[List[Endpoint]] = []
        completed: Set[str] = set()
        
        while remaining:
            # Find endpoints with all dependencies satisfied
            ready = []
            for path in list(remaining):
                deps = self._deps.get(path, set())
                if deps.issubset(completed):
                    ready.append(path)
            
            if not ready:
                # Circular dependency or missing dep - run remaining anyway
                ready = list(remaining)
            
            # Convert to Endpoint objects
            phase_endpoints = [endpoint_map[p] for p in ready if p in endpoint_map]
            if phase_endpoints:
                phases.append(phase_endpoints)
            
            completed.update(ready)
            remaining -= set(ready)
        
        return phases
    
    def should_skip_due_to_failure(self, endpoint: str, failed: Set[str]) -> Optional[str]:
        """Check if endpoint should be skipped due to dependency failure."""
        for dep in self._deps.get(endpoint, []):
            if dep in failed and dep in self._critical:
                return f"Skipped: dependency {dep} failed"
        return None


class ParallelTestEngine:
    """
    High-performance parallel test execution.
    
    Features:
    - Health-first: /health, /metrics run first, abort if fail
    - Dependency-aware: respects endpoint dependencies
    - Parallel batches: concurrent HTTP requests
    - Connection pooling: reuse connections
    """
    
    def __init__(
        self,
        config: WalkConfig,
        max_concurrent: int = 10,
        timeout: float = 10.0,
        health_first: bool = True
    ):
        self.config = config
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.health_first = health_first
        self.dependency_graph = EndpointDependencyGraph()
        self.day_dir: Optional[Path] = None
        self._auth_token: Optional[str] = None
        self._setup_default_dependencies()
    
    def set_day_dir(self, day_dir: Path):
        """Set the output directory for the current day (screenshots, logs)."""
        self.day_dir = day_dir
    
    def _setup_default_dependencies(self):
        """Configure sensible default dependencies."""
        # Health endpoints run first and are critical
        self.dependency_graph.add_dependency("/health", [], is_critical=True)
        self.dependency_graph.add_dependency("/api/health", ["/health"], is_critical=True)
        self.dependency_graph.add_dependency("/metrics", ["/health"])
        
        # Auth is typically critical
        self.dependency_graph.add_dependency("/api/auth/*", [], is_critical=True)
        self.dependency_graph.add_dependency("/api/user/*", ["/api/auth/login"])
        
        # Group endpoints
        self.dependency_graph.add_group("/health", "health")
        self.dependency_graph.add_group("/metrics", "health")
        self.dependency_graph.add_group("/api/health", "health")
    
    async def execute(self, endpoints: List[Endpoint]) -> List[EndpointResult]:
        """
        Execute all endpoint tests with parallelization.
        """
        await self._login_if_configured()
        if not endpoints:
            return []
        
        # Separate health endpoints
        health_eps = [ep for ep in endpoints if self._is_health_endpoint(ep)]
        other_eps = [ep for ep in endpoints if not self._is_health_endpoint(ep)]
        
        results: Dict[str, EndpointResult] = {}
        failed: Set[str] = set()
        
        # Phase 1: Health checks (sequential, critical)
        if self.health_first and health_eps:
            health_results = await self._run_batch(health_eps, sequential=True)
            for r in health_results:
                results[r.endpoint.path] = r
                if r.status != EndpointStatus.OK:
                    failed.add(r.endpoint.path)
            
            # Abort if health fails
            if failed:
                # Mark remaining as skipped
                for ep in other_eps:
                    results[ep.path] = EndpointResult(
                        endpoint=ep,
                        status=EndpointStatus.SKIP,
                        error="Health checks failed - skipping remaining tests",
                        response_time_ms=0
                    )
                return list(results.values())
        
        # Phase 2: Other endpoints (grouped by dependency)
        phases = self.dependency_graph.get_execution_order(other_eps)
        
        for phase in phases:
            # Filter out skipped endpoints
            to_run = []
            for ep in phase:
                skip_reason = self.dependency_graph.should_skip_due_to_failure(ep.path, failed)
                if skip_reason:
                    results[ep.path] = EndpointResult(
                        endpoint=ep,
                        status=EndpointStatus.SKIP,
                        error=skip_reason,
                        response_time_ms=0
                    )
                else:
                    to_run.append(ep)
            
            if to_run:
                batch_results = await self._run_batch(to_run, sequential=False)
                for r in batch_results:
                    results[r.endpoint.path] = r
                    if r.status != EndpointStatus.OK:
                        failed.add(r.endpoint.path)
        
        return list(results.values())
    
    def _is_health_endpoint(self, ep: Endpoint) -> bool:
        """Check if endpoint is a health check."""
        path_lower = ep.path.lower()
        return any(h in path_lower for h in ['/health', '/ping', '/ready', '/alive', '/status'])

    async def _login_if_configured(self) -> None:
        """Perform login to obtain Bearer token if configured."""
        if not self.config.login_url or not self.config.login_payload:
            return
        if self._auth_token:
            return  # Already logged in

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.config.login_url, json=self.config.login_payload)
                if resp.status_code == 200:
                    data = resp.json()
                    # Try common token field names
                    token = data.get("access_token") or data.get("token") or data.get("auth_token")
                    if token:
                        self._auth_token = token
        except Exception:
            pass  # Login failed, continue without token
    
    async def _run_batch(
        self,
        endpoints: List[Endpoint],
        sequential: bool = False
    ) -> List[EndpointResult]:
        """Run a batch of endpoint tests."""
        headers = dict(self.config.auth) if getattr(self.config, "auth", None) else {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        
        limits = httpx.Limits(
            max_connections=self.max_concurrent * 2,
            max_keepalive_connections=self.max_concurrent
        )
        
        async with httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.timeout,
            limits=limits,
            headers=headers,
            follow_redirects=True
        ) as client:
            
            if sequential:
                results = []
                for ep in endpoints:
                    result = await self._test_single(client, ep)
                    results.append(result)
                    # Early abort on critical failure
                    if result.status != EndpointStatus.OK and self._is_health_endpoint(ep):
                        return results
                return results
            else:
                # Parallel execution
                semaphore = asyncio.Semaphore(self.max_concurrent)
                
                async def run_with_limit(ep: Endpoint) -> EndpointResult:
                    async with semaphore:
                        return await self._test_single(client, ep)
                
                tasks = [run_with_limit(ep) for ep in endpoints]
                return await asyncio.gather(*tasks)
    
    async def _test_single(self, client: httpx.AsyncClient, endpoint: Endpoint) -> EndpointResult:
        """Test a single endpoint."""
        start = time.perf_counter()
        
        try:
            method = endpoint.method.upper() if endpoint.method else "GET"
            body = endpoint.body if isinstance(endpoint.body, dict) else None
            
            if method == "GET":
                response = await client.get(endpoint.path)
            elif method == "POST":
                response = await client.post(endpoint.path, json=body)
            elif method == "PUT":
                response = await client.put(endpoint.path, json=body)
            elif method == "PATCH":
                response = await client.patch(endpoint.path, json=body)
            elif method == "DELETE":
                response = await client.delete(endpoint.path)
            else:
                response = await client.request(method, endpoint.path)
            
            duration = time.perf_counter() - start
            
            # Determine status
            if response.status_code < 400:
                status = EndpointStatus.OK
            elif response.status_code < 500:
                status = EndpointStatus.FAIL  # Client error = fail
            else:
                status = EndpointStatus.FAIL  # Server error = fail
            
            return EndpointResult(
                endpoint=endpoint,
                status=status,
                http_status=response.status_code,
                error=response.text[:500] if status != EndpointStatus.OK else None,
                response_time_ms=duration * 1000
            )
            
        except httpx.TimeoutException:
            return EndpointResult(
                endpoint=endpoint,
                status=EndpointStatus.TIMEOUT,
                error=f"Timeout after {self.timeout}s",
                response_time_ms=(time.perf_counter() - start) * 1000
            )
        except Exception as e:
            return EndpointResult(
                endpoint=endpoint,
                status=EndpointStatus.FAIL,
                error=str(e)[:200],
                response_time_ms=(time.perf_counter() - start) * 1000
            )
    
    def execute_sync(self, endpoints: List[Endpoint]) -> List[EndpointResult]:
        """Synchronous wrapper for execute."""
        return asyncio.run(self.execute(endpoints))
