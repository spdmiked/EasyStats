from __future__ import annotations

import asyncio
import math
from datetime import UTC, datetime
from typing import Any

from ..config import RETAIL_SPEC_IDS, Settings
from ..models import CharacterRef, CharacterSnapshot, ItemVariant, Run, RunQuery
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
            "raiderio", f"{self.BASE}/mythic-plus/runs",
            params=self._params({"region": "us", "page": 0}),
            cache_key="season:current-runs",
        )
        season = data.get("season")
        if isinstance(season, dict):
            season = season.get("slug") or season.get("name")
        rankings = data.get("rankings", data.get("runs", []))
        if not season and rankings:
            first = rankings[0].get("run", rankings[0])
            season = first.get("season") or first.get("season_slug")
            if isinstance(season, dict):
                season = season.get("slug") or season.get("name")
        if not season:
            raise ValueError("Raider.IO did not expose the current season in its runs response")
        return str(season)

    async def get_top_runs(self, request: RunQuery) -> list[Run]:
        # The documented runs response already includes the roster, spec and complete
        # run loadout. Scan deeper pages until rare specs reach their regional share of
        # the target, then enrich only the selected characters through Blizzard.
        regional_target = math.ceil(
            self.settings.target_per_spec * self.settings.candidate_multiplier
            / len(self.settings.regions)
        )
        unique: dict[int, set[str]] = {spec_id: set() for spec_id in RETAIL_SPEC_IDS}
        result: list[Run] = []
        batch_size = 10
        for start in range(0, self.settings.raiderio_pages_per_region, batch_size):
            stop = min(start + batch_size, self.settings.raiderio_pages_per_region)
            pages = await asyncio.gather(*(
                self.client.request_json(
                    "raiderio", f"{self.BASE}/mythic-plus/runs",
                    params=self._params({
                        "region": request.region, "season": request.season, "page": page,
                    }),
                    cache_key=f"runs:{request.region}:{request.season}:{page}",
                )
                for page in range(start, stop)
            ))
            summaries = [
                raw.get("run", raw)
                for data in pages
                for raw in data.get("rankings", data.get("runs", []))
            ]
            for run in summaries:
                parsed = self._parse_run(run, request)
                if parsed is None:
                    continue
                contributes = any(
                    member.spec_id in unique
                    and member.privacy_key not in unique[member.spec_id]
                    and len(unique[member.spec_id]) < regional_target
                    for member in parsed.members
                )
                if not contributes:
                    continue
                result.append(parsed)
                for member in parsed.members:
                    if member.spec_id in unique and len(unique[member.spec_id]) < regional_target:
                        unique[member.spec_id].add(member.privacy_key)
            if all(len(characters) >= regional_target for characters in unique.values()):
                break
        details = await asyncio.gather(*(
            self.client.request_json(
                "raiderio", f"{self.BASE}/mythic-plus/run-details",
                params=self._params({"season": request.season, "id": int(run.run_id)}),
                cache_key=f"run-details:{request.season}:{run.run_id}",
            )
            for run in result if run.run_id
        ), return_exceptions=True)
        enriched: list[Run] = []
        for fallback, detail in zip(result, details, strict=True):
            parsed = None if isinstance(detail, BaseException) else self._parse_run(detail, request)
            enriched.append(parsed or fallback)
        return enriched

    def _parse_run(self, run: dict[str, Any], request: RunQuery) -> Run | None:
        try:
            completed = datetime.fromisoformat(str(run["completed_at"]))
            members_list: list[CharacterRef] = []
            for member in run.get("roster", run.get("members", [])):
                character = member.get("character", member)
                region = character.get("region", request.region)
                if isinstance(region, dict):
                    region = region.get("slug", request.region)
                realm = character.get("realm", "")
                if isinstance(realm, dict):
                    realm = realm.get("slug", realm.get("name", ""))
                spec = character.get("spec", {})
                loadout = character.get("talentLoadout") or {}
                items = member.get("items", {}).get("items", {})
                slots = tuple(
                    items[slot]
                    for slot in ("trinket1", "trinket2")
                    if items.get(slot, {}).get("item_id")
                )
                variants = tuple(ItemVariant(
                    item_id=int(item["item_id"]), item_level=int(item.get("item_level", 0)),
                    bonuses=tuple(int(value) for value in item.get("bonuses", []) if int(value) > 0),
                ) for item in slots)
                members_list.append(CharacterRef(
                    region=str(region), realm=str(realm), name=str(character.get("name", "")),
                    spec_id=int(spec.get("id", loadout.get("specId", 0))),
                    level=int(character.get("level", 0)),
                    talent_import=loadout.get("loadoutText") or member.get("loadout"),
                    trinkets=tuple(item.item_id for item in variants),
                    trinket_variants=variants,
                ))
            members = tuple(member for member in members_list if member.name and member.realm)
            return Run(
                run_id=str(run.get("id", run.get("keystone_run_id", ""))), season=request.season,
                completed_at=completed.astimezone(UTC),
                key_level=int(run.get("mythic_level", run.get("keystone_level", 0))),
                timed=float(run.get("clear_time_ms", 1)) <= float(
                    run.get("keystone_time_ms", run.get("par_time_ms", 0))
                ),
                members=members,
            )
        except (KeyError, TypeError, ValueError):
            return None

    async def get_character_snapshot(
        self, character: CharacterRef, run: Run
    ) -> CharacterSnapshot | None:
        return CharacterSnapshot(
            character=character, spec_id=character.spec_id, level=character.level,
            observed_at=run.completed_at, season=run.season, trinkets=character.trinkets,
            trinket_variants=character.trinket_variants,
            talent_import=character.talent_import, snapshot_quality=0.9,
        )
