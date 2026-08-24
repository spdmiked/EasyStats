from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class RunQuery:
    season: str
    region: str
    since: datetime


@dataclass(frozen=True, slots=True)
class CharacterRef:
    region: str
    realm: str
    name: str

    @property
    def privacy_key(self) -> str:
        return f"{self.region}:{self.realm.casefold()}:{self.name.casefold()}"


@dataclass(frozen=True, slots=True)
class Run:
    run_id: str
    season: str
    completed_at: datetime
    key_level: int
    timed: bool
    members: tuple[CharacterRef, ...]


@dataclass(frozen=True, slots=True)
class CharacterSnapshot:
    character: CharacterRef
    spec_id: int
    level: int
    observed_at: datetime
    season: str
    crit: int | None = None
    haste: int | None = None
    mastery: int | None = None
    versatility: int | None = None
    trinkets: tuple[int, ...] = ()
    talent_import: str | None = None
    snapshot_quality: float = 1.0


@dataclass(frozen=True, slots=True)
class Observation:
    snapshot: CharacterSnapshot
    run: Run
    weight: float = 1.0


class RunProvider(Protocol):
    async def get_current_season(self) -> str: ...
    async def get_top_runs(self, request: RunQuery) -> list[Run]: ...
    async def get_character_snapshot(
        self, character: CharacterRef, run: Run
    ) -> CharacterSnapshot | None: ...


@dataclass(slots=True)
class CategoryResult:
    value: dict[str, Any]
    sample_size: int
    generated_at: int
    stale: bool = False


@dataclass(slots=True)
class SpecResult:
    stats: CategoryResult | None = None
    trinkets: CategoryResult | None = None
    talents: CategoryResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Database:
    schema_version: int
    generated_at: int
    game_version: str
    season_slug: str
    source_mode: str
    specs: dict[int, SpecResult]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

