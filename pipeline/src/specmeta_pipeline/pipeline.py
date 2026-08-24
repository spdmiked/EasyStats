from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from .cache import DiskCache
from .config import Settings
from .models import (
    CharacterRef,
    CharacterSnapshot,
    Observation,
    Run,
    RunProvider,
    RunQuery,
    utc_now,
)
from .providers import BlizzardProvider, RaiderIOProvider
from .providers.base import APIClient, ProviderError


async def _collect(
    provider: RunProvider, settings: Settings, season: str,
    enrichment: RunProvider | None = None,
) -> list[Observation]:
    observations: list[Observation] = []
    for region in settings.regions:
        runs = await provider.get_top_runs(RunQuery(season, region, utc_now() - timedelta(days=settings.max_age_days)))
        eligible = [run for run in runs if run.timed and run.completed_at >= utc_now() - timedelta(days=settings.max_age_days)]
        async def snapshot(member: CharacterRef, run: Run) -> CharacterSnapshot | None:
            primary = await provider.get_character_snapshot(member, run)
            if primary is None or enrichment is None:
                return primary
            secondary = await enrichment.get_character_snapshot(member, run)
            if secondary is None or secondary.spec_id not in {0, primary.spec_id}:
                return primary
            return replace(
                primary, crit=secondary.crit, haste=secondary.haste,
                mastery=secondary.mastery, versatility=secondary.versatility,
                snapshot_quality=min(primary.snapshot_quality, secondary.snapshot_quality),
            )

        tasks = [snapshot(member, run) for run in eligible for member in run.members]
        snapshots = await asyncio.gather(*tasks, return_exceptions=True)
        cursor = 0
        for run in eligible:
            for _member in run.members:
                snapshot = snapshots[cursor]
                cursor += 1
                if not isinstance(snapshot, BaseException) and snapshot is not None:
                    observations.append(Observation(snapshot, run))
    return observations


async def collect_live(settings: Settings, cache_root: Path) -> tuple[str, list[Observation], list[str]]:
    cache = DiskCache(cache_root, settings.cache_ttl_seconds)
    client = APIClient(cache, settings.request_timeout, settings.max_retries, settings.max_concurrency)
    errors: list[str] = []
    try:
        blizzard = None
        if settings.blizzard_client_id and settings.blizzard_client_secret:
            blizzard = BlizzardProvider(settings, client)
        raiderio = RaiderIOProvider(settings, client)
        if settings.provider == "blizzard":
            if blizzard is None:
                raise ProviderError("Blizzard credentials are required")
            season = await blizzard.get_current_season()
            return season, await _collect(blizzard, settings, season), errors
        try:
            season = await raiderio.get_current_season()
            rows = await _collect(
                raiderio, settings, season,
                blizzard if settings.provider == "hybrid" else None,
            )
            # Hybrid validation/enrichment is intentionally conservative: current official profile
            # data may supplement missing fields, but never overwrites a run snapshot.
            if settings.provider == "hybrid" and not rows and blizzard is not None:
                errors.append("Raider.IO produced no usable observations; attempted Blizzard fallback")
                return season, await _collect(blizzard, settings, season), errors
            return season, rows, errors
        except Exception as exc:
            if settings.provider != "hybrid" or blizzard is None:
                raise
            errors.append(f"Raider.IO unavailable: {type(exc).__name__}")
            season = await blizzard.get_current_season()
            return season, await _collect(blizzard, settings, season), errors
    finally:
        await client.close()
