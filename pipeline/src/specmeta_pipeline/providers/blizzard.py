from __future__ import annotations

import asyncio
import base64
import time
from datetime import datetime
from typing import Any

import httpx

from ..config import Settings
from ..models import CharacterRef, CharacterSnapshot, Run, RunQuery
from .base import APIClient, ProviderError


class BlizzardProvider:
    """Official Battle.net API provider; leaderboards discover runs, profiles enrich them."""

    def __init__(self, settings: Settings, client: APIClient) -> None:
        if not settings.blizzard_client_id or not settings.blizzard_client_secret:
            raise ProviderError("BLIZZARD_CLIENT_ID and BLIZZARD_CLIENT_SECRET are required")
        self.settings = settings
        self.client = client
        self._token: str | None = None
        self._expires_at = 0.0
        self._token_lock = asyncio.Lock()

    async def _access_token(self) -> str:
        if self._token and time.time() < self._expires_at - 60:
            return self._token
        async with self._token_lock:
            if self._token and time.time() < self._expires_at - 60:
                return self._token
            raw = f"{self.settings.blizzard_client_id}:{self.settings.blizzard_client_secret}"
            auth = base64.b64encode(raw.encode()).decode()
            response = await self.client.client.post(
                "https://oauth.battle.net/token",
                data={"grant_type": "client_credentials"},
                headers={"Authorization": f"Basic {auth}"},
            )
            response.raise_for_status()
            payload = response.json()
            self._token = str(payload["access_token"])
            self._expires_at = time.time() + int(payload.get("expires_in", 86400))
            return self._token

    async def _get(self, region: str, path: str, params: dict[str, Any]) -> Any:
        token = await self._access_token()
        params = {**params, "access_token": token}
        return await self.client.request_json(
            "blizzard", f"https://{region}.api.blizzard.com{path}", params=params,
            cache_key=f"{region}:{path}:{sorted((k, v) for k, v in params.items() if k != 'access_token')}",
        )

    async def get_current_season(self) -> str:
        data = await self._get("us", "/data/wow/mythic-keystone/season/index", {
            "namespace": "dynamic-us", "locale": "en_US",
        })
        seasons = data.get("seasons", [])
        if not seasons:
            raise ProviderError("Blizzard returned no Mythic+ seasons")
        return str(seasons[-1]["id"])

    async def get_top_runs(self, request: RunQuery) -> list[Run]:
        # Blizzard exposes connected-realm leaderboards, but enumerating all realms/dungeons is
        # deliberately delegated to a future official catalog adapter. Hybrid mode uses Raider.IO.
        return []

    async def get_character_snapshot(
        self, character: CharacterRef, run: Run
    ) -> CharacterSnapshot | None:
        region = character.region.lower()
        realm = character.realm.lower().replace(" ", "-")
        name = character.name.lower()
        base = f"/profile/wow/character/{realm}/{name}"
        params = {"namespace": f"profile-{region}", "locale": "en_US"}
        if character.spec_id > 0 and character.level > 0:
            try:
                statistics = await self._get(region, f"{base}/statistics", params)
            except (ProviderError, httpx.HTTPStatusError):
                return None
            return CharacterSnapshot(
                character=character,
                spec_id=character.spec_id,
                level=character.level,
                observed_at=run.completed_at,
                season=run.season,
                crit=(
                    statistics.get("melee_crit", {})
                    or statistics.get("spell_crit", {})
                ).get("rating"),
                haste=(
                    statistics.get("melee_haste", {})
                    or statistics.get("spell_haste", {})
                ).get("rating"),
                mastery=statistics.get("mastery", {}).get("rating"),
                versatility=statistics.get("versatility"),
                snapshot_quality=0.55,
            )
        try:
            profile = await self._get(region, base, params)
            statistics = await self._get(region, f"{base}/statistics", params)
            equipment = await self._get(region, f"{base}/equipment", params)
            specs = await self._get(region, f"{base}/specializations", params)
        except (ProviderError, httpx.HTTPStatusError):
            return None
        active = next((
            s for s in specs.get("specializations", [])
            if int(s.get("specialization", {}).get("id", 0)) == character.spec_id
        ), None)
        if active is None:
            active = next((s for s in specs.get("specializations", []) if s.get("loadouts")), None)
        spec_id = int((active or {}).get("specialization", {}).get("id", 0))
        items = equipment.get("equipped_items", [])
        trinkets = tuple(
            int(item["item"]["id"])
            for item in items
            if item.get("slot", {}).get("type") in {"TRINKET_1", "TRINKET_2"}
        )
        stats = statistics
        return CharacterSnapshot(
            character=character, spec_id=spec_id, level=int(profile.get("level", character.level)),
            observed_at=datetime.fromtimestamp(run.completed_at.timestamp(), run.completed_at.tzinfo),
            season=run.season,
            crit=(stats.get("melee_crit", {}) or stats.get("spell_crit", {})).get("rating"),
            haste=(stats.get("melee_haste", {}) or stats.get("spell_haste", {})).get("rating"),
            mastery=stats.get("mastery", {}).get("rating"),
            versatility=stats.get("versatility"),
            trinkets=trinkets, talent_import=None, snapshot_quality=0.55,
        )
