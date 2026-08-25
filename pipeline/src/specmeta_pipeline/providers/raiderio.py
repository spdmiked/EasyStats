from __future__ import annotations

import asyncio
import math
from datetime import UTC, datetime
from typing import Any

from ..config import RETAIL_SPEC_IDS, RETAIL_SPEC_SLUGS, Settings
from ..models import CharacterRef, CharacterSnapshot, ItemVariant, Run, RunQuery
from .base import APIClient


class RaiderIOProvider:
    """Raider.IO run API plus its public specialization leaderboard."""

    BASE = "https://raider.io/api/v1"
    SPEC_RANKINGS = "https://raider.io/api/mythic-plus/rankings/specs"

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
        # The official website's specialization leaderboard is the only Raider.IO
        # ranking surface that reliably selects every spec. It is used only for
        # candidate discovery; Blizzard supplies stats/equipment in hybrid mode.
        regional_target = math.ceil(
            self.settings.target_per_spec / len(self.settings.regions)
        )
        leaderboard_runs = await self._get_spec_leaderboard_runs(request, regional_target)
        counts: dict[int, int] = {spec_id: 0 for spec_id in RETAIL_SPEC_IDS}
        for run in leaderboard_runs:
            for member in run.members:
                counts[member.spec_id] = counts.get(member.spec_id, 0) + 1
        missing = {spec_id for spec_id, count in counts.items() if count < regional_target}
        if not missing:
            return leaderboard_runs

        # A newly added leaderboard can briefly mix another spec into its first rows
        # (observed for Devourer during Midnight). Never accept that mismatch; fill
        # only a remaining shortfall from the documented overall-runs API.
        fallback = await self._get_overall_runs(request, regional_target, missing, counts)
        return [*leaderboard_runs, *fallback]

    async def _get_spec_leaderboard_runs(
        self, request: RunQuery, regional_target: int,
    ) -> list[Run]:
        pages = max(1, math.ceil(regional_target / 100))
        jobs = [
            (spec_id, page, self.client.request_json(
                "raiderio-leaderboard", self.SPEC_RANKINGS,
                params={
                    "region": request.region, "season": request.season,
                    "class": class_slug, "spec": spec_slug, "page": page,
                },
                cache_key=(
                    f"spec-rankings:{request.region}:{request.season}:"
                    f"{class_slug}:{spec_slug}:{page}"
                ),
            ))
            for spec_id, (class_slug, spec_slug) in RETAIL_SPEC_SLUGS.items()
            for page in range(pages)
        ]
        payloads = await asyncio.gather(*(job for _, _, job in jobs), return_exceptions=True)
        seen: dict[int, set[str]] = {spec_id: set() for spec_id in RETAIL_SPEC_IDS}
        result: list[Run] = []
        observed_at = datetime.now(UTC)
        for (requested_spec, _, _), payload in zip(jobs, payloads, strict=True):
            if isinstance(payload, BaseException):
                continue
            rankings = payload.get("rankings", {})
            for row in rankings.get("rankedCharacters", []):
                parsed = self._parse_leaderboard_row(
                    row, request, requested_spec, observed_at,
                )
                if parsed is None:
                    continue
                member = parsed.members[0]
                if (member.privacy_key in seen[requested_spec]
                        or len(seen[requested_spec]) >= regional_target):
                    continue
                seen[requested_spec].add(member.privacy_key)
                result.append(parsed)
        return result

    def _parse_leaderboard_row(
        self, row: dict[str, Any], request: RunQuery, requested_spec: int,
        observed_at: datetime,
    ) -> Run | None:
        try:
            character = row["character"]
            spec_id = int(character["spec"]["id"])
            if spec_id != requested_spec:
                return None
            region = character["region"]["slug"]
            realm = character["realm"]["slug"]
            best = max(
                row.get("runs", []),
                key=lambda run: (
                    int(run.get("mythicLevel", 0)), float(run.get("score", 0)),
                ),
            )
            member = CharacterRef(
                region=str(region), realm=str(realm), name=str(character["name"]),
                spec_id=spec_id, level=int(character.get("level", 0)),
                talent_import=character.get("talentLoadoutText"),
            )
            return Run(
                run_id=str(best["keystoneRunId"]), season=request.season,
                completed_at=observed_at, key_level=int(best["mythicLevel"]),
                timed=int(best["clearTimeMs"]) <= int(best["parTimeMs"]),
                members=(member,),
            )
        except (KeyError, TypeError, ValueError):
            return None

    async def _get_overall_runs(
        self, request: RunQuery, regional_target: int, missing: set[int],
        initial_counts: dict[int, int],
    ) -> list[Run]:
        unique: dict[int, set[str]] = {spec_id: set() for spec_id in RETAIL_SPEC_IDS}
        counts = dict(initial_counts)
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
                selected_members = tuple(
                    member for member in parsed.members
                    if (member.spec_id in missing
                        and member.privacy_key not in unique[member.spec_id]
                        and counts[member.spec_id] < regional_target)
                )
                if not selected_members:
                    continue
                result.append(Run(
                    parsed.run_id, parsed.season, parsed.completed_at,
                    parsed.key_level, parsed.timed, selected_members,
                ))
                for member in selected_members:
                    unique[member.spec_id].add(member.privacy_key)
                    counts[member.spec_id] += 1
            if all(counts[spec_id] >= regional_target for spec_id in missing):
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
            if parsed is None:
                enriched.append(fallback)
                continue
            wanted = {member.privacy_key for member in fallback.members}
            members = tuple(member for member in parsed.members if member.privacy_key in wanted)
            enriched.append(Run(
                parsed.run_id, parsed.season, parsed.completed_at,
                parsed.key_level, parsed.timed, members,
            ))
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
