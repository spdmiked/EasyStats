from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import CharacterRef, CharacterSnapshot, Observation, Run


def sample_observations(size: int = 48, spec_id: int = 253) -> list[Observation]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    result = []
    builds = ("B" + "A" * 30, "B" + "C" * 30, "B" + "D" * 30)
    for index in range(size):
        character = CharacterRef(("eu", "us", "kr", "tw")[index % 4], "fixture-realm", f"fixture-{index}")
        completed = now - timedelta(hours=index % 72)
        run = Run(f"fixture-run-{index}", "fixture-season", completed, 10 + index % 8, True, (character,))
        snapshot = CharacterSnapshot(
            character, spec_id, 90, completed, "fixture-season",
            crit=1800 + index * 2, haste=3100 + index * 3, mastery=2600 + index,
            versatility=1300 + index, trinkets=(100001 + index % 5, 100006 + index % 3),
            talent_import=builds[0 if index < 25 else 1 if index < 39 else 2], snapshot_quality=1.0,
        )
        result.append(Observation(snapshot, run))
    return result
