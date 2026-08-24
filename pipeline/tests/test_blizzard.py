import asyncio
from pathlib import Path

import httpx
import pytest

from specmeta_pipeline.cache import DiskCache
from specmeta_pipeline.config import Settings
from specmeta_pipeline.providers.base import APIClient
from specmeta_pipeline.providers.blizzard import BlizzardProvider


@pytest.mark.asyncio
async def test_oauth_token_is_reused(tmp_path: Path) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if request.url.path == "/token":
            assert request.headers["Authorization"].startswith("Basic ")
            return httpx.Response(
                200,
                json={"access_token": "fixture-token", "expires_in": 3600},
                request=request,
            )
        assert request.headers["Authorization"] == "Bearer fixture-token"
        assert "access_token" not in request.url.params
        return httpx.Response(200, json={"melee_crit": {"rating": 123}}, request=request)

    api = APIClient(DiskCache(tmp_path), 1, 0, 1)
    await api.client.aclose()
    api.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = BlizzardProvider(Settings(blizzard_client_id="id", blizzard_client_secret="secret"), api)
    tokens = await asyncio.gather(*(provider._access_token() for _ in range(20)))
    assert tokens == ["fixture-token"] * 20
    stats = await provider._get(
        "us",
        "/profile/wow/character/realm/name/statistics",
        {"namespace": "profile-us"},
    )
    assert stats["melee_crit"]["rating"] == 123
    assert calls == 2
    await api.close()
