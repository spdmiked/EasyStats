from pathlib import Path

import httpx
import pytest

from specmeta_pipeline.cache import DiskCache
from specmeta_pipeline.providers.base import APIClient


@pytest.mark.asyncio
async def test_429_retry_after(tmp_path: Path) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, request=request)
        return httpx.Response(200, json={"ok": True}, request=request)

    client = APIClient(DiskCache(tmp_path), 1, 2, 1)
    await client.client.aclose()
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    assert await client.request_json("test", "https://example.invalid") == {"ok": True}
    assert calls == 2
    await client.close()


def test_cache_does_not_store_secret_in_filename(tmp_path: Path) -> None:
    cache = DiskCache(tmp_path)
    cache.set("api", "Authorization: secret", {"ok": True})
    names = [path.name for path in tmp_path.rglob("*")]
    assert all("secret" not in name for name in names)
