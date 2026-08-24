from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx

from ..cache import DiskCache


class ProviderError(RuntimeError):
    pass


class APIClient:
    def __init__(self, cache: DiskCache, timeout: float, retries: int, concurrency: int) -> None:
        self.cache = cache
        self.retries = retries
        self.semaphore = asyncio.Semaphore(concurrency)
        self.client = httpx.AsyncClient(timeout=timeout)

    async def request_json(
        self, namespace: str, url: str, *, params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None, cache_key: str | None = None,
    ) -> Any:
        key = cache_key or f"{url}:{sorted((params or {}).items())}"
        cached = self.cache.get(namespace, key)
        if cached is not None:
            return cached
        for attempt in range(self.retries + 1):
            try:
                async with self.semaphore:
                    response = await self.client.get(url, params=params, headers=headers)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt >= self.retries:
                        raise ProviderError(f"Transient API failure: HTTP {response.status_code}")
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt + random.random()
                    await asyncio.sleep(min(delay, 30.0))
                    continue
                response.raise_for_status()
                data = response.json()
                self.cache.set(namespace, key, data, response.headers.get("ETag"))
                return data
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt >= self.retries:
                    raise ProviderError("API request exhausted retries") from exc
                await asyncio.sleep(min(2**attempt + random.random(), 30.0))
        raise ProviderError("Unreachable request state")

    async def close(self) -> None:
        await self.client.aclose()

