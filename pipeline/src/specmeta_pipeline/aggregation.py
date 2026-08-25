from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime

from .config import Settings
from .models import CategoryResult, Observation, SpecResult

STATS = ("CRIT", "HASTE", "MASTERY", "VERSATILITY")
TALENT_RE = re.compile(r"^[A-Za-z0-9+/=_-]{20,2048}$")


def weighted_median(values: Sequence[tuple[float, float]]) -> float:
    if not values:
        raise ValueError("weighted_median requires values")
    ordered = sorted(values)
    total = sum(max(weight, 0.0) for _, weight in ordered)
    cursor = 0.0
    for value, weight in ordered:
        cursor += max(weight, 0.0)
        if cursor >= total / 2:
            return value
    return ordered[-1][0]


def _percentile(values: Sequence[int], fraction: float) -> int:
    ordered = sorted(values)
    if not ordered:
        return 0
    return ordered[min(len(ordered) - 1, math.floor((len(ordered) - 1) * fraction))]


def prepare_observations(rows: Iterable[Observation], settings: Settings, season: str) -> list[Observation]:
    now = datetime.now(UTC)
    candidates = [r for r in rows if r.run.timed and r.run.season == season]
    thresholds: dict[int, int] = {}
    by_spec: dict[int, list[int]] = defaultdict(list)
    for row in candidates:
        by_spec[row.snapshot.spec_id].append(row.run.key_level)
    for spec, levels in by_spec.items():
        adaptive = _percentile(levels, settings.adaptive_percentile)
        descending = sorted(levels, reverse=True)
        sample_floor = descending[min(len(descending), settings.min_per_spec) - 1]
        thresholds[spec] = min(adaptive, sample_floor)
    seen: set[tuple[str, int, str]] = set()
    accepted: list[Observation] = []
    for row in sorted(candidates, key=lambda r: (-r.run.key_level, r.run.completed_at)):
        snap = row.snapshot
        age_days = (now - snap.observed_at).total_seconds() / 86400
        bucket = snap.observed_at.strftime("%Y-%m-%d")
        key = (snap.character.privacy_key, snap.spec_id, bucket)
        if (snap.spec_id <= 0 or snap.level != settings.max_character_level
                or age_days > settings.max_age_days or key in seen):
            continue
        if row.run.key_level < thresholds.get(snap.spec_id, 0):
            continue
        seen.add(key)
        recency = max(0.25, 1.0 - age_days / (settings.max_age_days * 1.25))
        key_weight = 1.0 + max(0, row.run.key_level - thresholds[snap.spec_id]) * 0.04
        accepted.append(Observation(snap, row.run, key_weight * recency * snap.snapshot_quality))
    return accepted


def aggregate_stats(rows: Sequence[Observation], now: int) -> CategoryResult | None:
    values: dict[str, list[tuple[float, float]]] = defaultdict(list)
    valid = 0
    for row in rows:
        raw = (row.snapshot.crit, row.snapshot.haste, row.snapshot.mastery, row.snapshot.versatility)
        if any(v is None or v < 0 for v in raw):
            continue
        normalized = tuple(int(v) for v in raw if v is not None)
        total = sum(normalized)
        if total <= 0:
            continue
        valid += 1
        for name, value in zip(STATS, normalized, strict=True):
            values[name].append((value / total, row.weight))
    if not valid:
        return None
    scores = {name: weighted_median(values[name]) for name in STATS}
    order = sorted(STATS, key=lambda name: (-scores[name], name))
    return CategoryResult({"order": order, "scores": scores}, valid, now)


def add_stat_separators(category: CategoryResult, tie_threshold: float) -> None:
    order = category.value["order"]
    scores = category.value["scores"]
    category.value["separators"] = [
        "≈" if abs(scores[order[i]] - scores[order[i + 1]]) < tie_threshold else ">"
        for i in range(len(order) - 1)
    ]


def aggregate_trinkets(
    rows: Sequence[Observation], now: int, canonical: dict[int, int] | None = None
) -> CategoryResult | None:
    canonical = canonical or {}
    counts: dict[int, float] = defaultdict(float)
    strongest: dict[int, tuple[int, tuple[int, ...]]] = {}
    voters = 0
    for row in rows:
        items = {canonical.get(item, item) for item in row.snapshot.trinkets if item > 0}
        if not items:
            continue
        voters += 1
        for item in items:
            counts[item] += row.weight
        for variant in row.snapshot.trinket_variants:
            item = canonical.get(variant.item_id, variant.item_id)
            candidate = (variant.item_level, variant.bonuses)
            if candidate > strongest.get(item, (0, ())):
                strongest[item] = candidate
    if not voters:
        return None
    total_weight = sum(row.weight for row in rows if row.snapshot.trinkets)
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:4]
    rendered = []
    for item, weight in ranked:
        item_level, bonuses = strongest.get(item, (0, ()))
        rendered.append({
            "itemID": item, "usage": weight / total_weight,
            "itemLevel": item_level, "bonuses": list(bonuses),
        })
    return CategoryResult({"items": rendered}, voters, now)


def normalize_talent(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = "".join(value.split())
    return normalized if TALENT_RE.fullmatch(normalized) else None


def aggregate_talents(
    rows: Sequence[Observation], now: int, voter_limit: int | None = None
) -> CategoryResult | None:
    counts: dict[str, float] = defaultdict(float)
    voters = 0
    total_weight = 0.0
    for row in rows:
        code = normalize_talent(row.snapshot.talent_import)
        if code is None:
            continue
        voters += 1
        total_weight += row.weight
        counts[code] += row.weight
        if voter_limit is not None and voters >= voter_limit:
            break
    if not voters:
        return None
    winner, weight = min(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return CategoryResult({"importString": winner, "support": weight / total_weight}, voters, now)


def aggregate_by_spec(rows: Sequence[Observation], settings: Settings, now: int) -> dict[int, SpecResult]:
    grouped: dict[int, list[Observation]] = defaultdict(list)
    for row in rows:
        grouped[row.snapshot.spec_id].append(row)
    output: dict[int, SpecResult] = {}
    for spec_id, spec_rows in sorted(grouped.items()):
        stats = aggregate_stats(spec_rows, now)
        if stats:
            add_stat_separators(stats, settings.tie_threshold)
        trinkets = aggregate_trinkets(spec_rows, now)
        # Exact import strings fragment quickly because optional utility choices vary.
        # Compare the highest-ranked complete cohort required by the methodology,
        # rather than diluting its winner with lower-ranked observations.
        talents = aggregate_talents(spec_rows, now, settings.min_talent_sample)
        if len(spec_rows) < settings.min_per_spec:
            stats = trinkets = None
        if talents and (talents.sample_size < settings.min_talent_sample or
                        talents.value["support"] < settings.min_build_support):
            talents = None
        output[spec_id] = SpecResult(stats, trinkets, talents, {"regionCount": 4, "methodologyVersion": 1})
    return output
