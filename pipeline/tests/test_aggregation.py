from datetime import UTC, datetime

from specmeta_pipeline.aggregation import (
    add_stat_separators,
    aggregate_stats,
    aggregate_talents,
    aggregate_trinkets,
    normalize_talent,
    prepare_observations,
    weighted_median,
)
from specmeta_pipeline.config import Settings
from specmeta_pipeline.fixtures import sample_observations
from specmeta_pipeline.models import CharacterRef, CharacterSnapshot, Observation, Run


def test_weighted_median() -> None:
    assert weighted_median([(1, 1), (2, 5), (3, 1)]) == 2


def test_deduplication_and_timed_filter() -> None:
    rows = sample_observations(48)
    duplicate = rows[0]
    untimed_run = Run("bad", duplicate.run.season, duplicate.run.completed_at, 99, False, duplicate.run.members)
    result = prepare_observations([*rows, duplicate, Observation(duplicate.snapshot, untimed_run)], Settings(), "fixture-season")
    keys = {(r.snapshot.character.privacy_key, r.snapshot.observed_at.strftime("%Y-%m-%d")) for r in result}
    assert len(keys) == len(result)
    assert all(row.run.timed for row in result)


def test_stats_tie_detection() -> None:
    rows = prepare_observations(sample_observations(48), Settings(), "fixture-season")
    result = aggregate_stats(rows, 123)
    assert result is not None
    result.value["scores"]["HASTE"] = 0.30
    result.value["scores"]["MASTERY"] = 0.29
    result.value["order"] = ["HASTE", "MASTERY", "CRIT", "VERSATILITY"]
    add_stat_separators(result, 0.025)
    assert result.value["separators"][0] == "≈"


def test_trinkets_are_unique_and_variants_merge() -> None:
    rows = sample_observations(48)
    result = aggregate_trinkets(rows, 123, {100006: 100001})
    assert result is not None
    ids = [item["itemID"] for item in result.value["items"]]
    assert len(ids) == len(set(ids)) == 4
    assert ids[0] == 100001


def test_talents_select_complete_loadout() -> None:
    result = aggregate_talents(sample_observations(48), 123)
    assert result is not None
    assert result.value["importString"] == "B" + "A" * 30
    assert result.value["support"] > 0.5
    assert normalize_talent("not valid nodes") is None


def test_zero_stats_are_rejected() -> None:
    now = datetime.now(UTC)
    ref = CharacterRef("eu", "r", "n")
    run = Run("1", "s", now, 10, True, (ref,))
    snap = CharacterSnapshot(ref, 253, 80, now, "s", 0, 0, 0, 0)
    assert aggregate_stats([Observation(snap, run)], 1) is None
