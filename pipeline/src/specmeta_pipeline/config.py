from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    provider: str = "hybrid"
    regions: tuple[str, ...] = ("eu", "us", "kr", "tw")
    target_per_spec: int = 150
    min_per_spec: int = 40
    max_per_spec: int = 300
    max_character_level: int = 90
    min_talent_sample: int = 40
    min_build_support: float = 0.15
    max_age_days: int = 14
    soft_stale_days: int = 7
    hard_stale_days: int = 30
    tie_threshold: float = 0.025
    adaptive_percentile: float = 0.65
    cache_ttl_seconds: int = 21600
    request_timeout: float = 20.0
    max_concurrency: int = 8
    max_retries: int = 4
    raiderio_pages_per_region: int = 10
    blizzard_client_id: str | None = None
    blizzard_client_secret: str | None = None
    raiderio_api_key: str | None = None

    @classmethod
    def from_env(cls) -> Settings:
        provider = os.getenv("DATA_PROVIDER", "hybrid").lower()
        if provider not in {"hybrid", "raiderio", "blizzard", "fixture"}:
            raise ValueError(f"Unsupported DATA_PROVIDER: {provider}")
        return cls(
            provider=provider,
            target_per_spec=int(os.getenv("TARGET_UNIQUE_CHARACTERS_PER_SPEC", "150")),
            min_per_spec=int(os.getenv("MIN_UNIQUE_CHARACTERS_PER_SPEC", "40")),
            max_per_spec=int(os.getenv("MAX_UNIQUE_CHARACTERS_PER_SPEC", "300")),
            max_character_level=int(os.getenv("MAX_CHARACTER_LEVEL", "90")),
            raiderio_pages_per_region=int(os.getenv("RAIDERIO_PAGES_PER_REGION", "10")),
            blizzard_client_id=os.getenv("BLIZZARD_CLIENT_ID"),
            blizzard_client_secret=os.getenv("BLIZZARD_CLIENT_SECRET"),
            raiderio_api_key=os.getenv("RAIDERIO_API_KEY"),
        )


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "addon" / "EasyStats" / "GeneratedData.lua"
DEFAULT_STATE = REPO_ROOT / "pipeline" / "state.json"
DEFAULT_REPORTS = REPO_ROOT / "reports"
