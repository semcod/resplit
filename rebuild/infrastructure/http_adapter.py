from __future__ import annotations
import httpx
import time
from typing import Optional, Any, Dict


class HttpAdapter:
    """
    Adapter for HTTP requests.
    Centralizes timeout, retry logic, and client management.
    """

    def __init__(self, timeout: int = 10, retries: int = 3):
        self.timeout = timeout
        self.retries = retries
        self.client = httpx.Client(timeout=timeout)

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        last_exc = None
        for attempt in range(self.retries):
            try:
                return self.client.get(url, params=params, headers=headers)
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exc = e
                time.sleep(2**attempt)  # Exponential backoff
        raise last_exc or Exception(f"Failed to GET {url}")

    def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        return self.client.post(url, json=json, headers=headers)

    def put(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        return self.client.put(url, json=json, headers=headers)

    def patch(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        return self.client.patch(url, json=json, headers=headers)

    def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        return self.client.delete(url, headers=headers)

    def close(self):
        self.client.close()
