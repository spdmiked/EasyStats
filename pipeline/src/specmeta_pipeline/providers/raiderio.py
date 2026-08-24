from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..config import Settings
from ..models import CharacterRef, CharacterSnapshot, Run, RunQuery
from .base import APIClient


class RaiderIOProvider:
    """Adapter for documented Raider.IO API endpoints."""

    BASE = "https://raider.io/api/v1"

    def __init__(self, settings: Settings, client: APIClient) -> None:
        self.settings = settings
        self.client = client

    def _params(self, values: dict[str, Any]) -> dict[str, Any]:
        if self.settings.raiderio_api_key:
            return {**values, "access_key": self.settings.raiderio_api_key}
        return values

    async def get_current_season(self) -> str:
        data = await self.client.request_json(
            "raiderio", f"{self.BASE}/mythic-plus/season-cutoffs",
            params=self._params({"region": "world", "season": "current"}),
            cache_key="season:current",
        )
        return str(data.get("season", "current"))

    async def get_top_runs(self, request: RunQuery) -> list[Run]:
        data = await self.client.request_json(
            "raiderio", f"{self.BASE}/mythic-plus/runs",
            params=self._params({"region": request.region, "season": request.season}),
            cache_key=f"runs:{request.region}:{request.season}",
        )
        result: list[Run] = []
        for raw in data.get("rankings", data.get("runs", [])):
            run = raw.get("run", raw)
            completed = datetime.fromisoformat(str(run["completed_at"]).replace("Z", "+00:00"))
            members = tuple(
                CharacterRef(
                    region=str(m.get("region", request.region)),
                    realm=str(m.get("realm", {}).get("slug", m.get("realm", ""))),
                    name=str(m.get("name", m.get("character", {}).get("name", ""))),
                )
                for m in run.get("roster", run.get("members", []))
            )
            result.append(Run(
                run_id=str(run.get("id", run.get("keystone_run_id", ""))), season=request.season,
                completed_at=completed.astimezone(timezone.utc),
                key_level=int(run.get("mythic_level", run.get("keystone_level", 0))),
                timed=float(run.get("clear_time_ms", 1)) <= float(run.get("par_time_ms", 0)),
                members=members,
            ))
        return result

    async def get_character_snapshot(
        self, character: CharacterRef, run: Run
    ) -> CharacterSnapshot | None:
        data = await self.client.request_json(
            "raiderio", f"{self.BASE}/characters/profile",
            params=self._params({
                "region": character.region, "realm": character.realm, "name": character.name,
                "fields": "gear,talents",
            }),
            cache_key=f"character:{character.privacy_key}",
        )
        gear = data.get("gear", {})
        items = gear.get("items", {})
        trinkets = tuple(
            int(items[k].get("item_id", 0)) for k in ("trinket1", "trinket2")
            if items.get(k, {}).get("item_id")
        )
        stats = gear.get("stats", {})
        return CharacterSnapshot(
            character=character, spec_id=int(data.get("active_spec_id", 0)),
            level=int(data.get("level", 0)), observed_at=run.completed_at, season=run.season,
            crit=stats.get("crit"), haste=stats.get("haste"), mastery=stats.get("mastery"),
            versatility=stats.get("versatility"), trinkets=trinkets,
            talent_import=data.get("talent_loadout_code"), snapshot_quality=0.65,
        )

