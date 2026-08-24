from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .config import Settings
from .models import CategoryResult, Database, SpecResult


def load_database(path: Path) -> Database | None:
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    specs: dict[int, SpecResult] = {}
    for key, value in raw.get("specs", {}).items():
        def category(name: str) -> CategoryResult | None:
            item = value.get(name)
            return CategoryResult(**item) if item else None
        specs[int(key)] = SpecResult(category("stats"), category("trinkets"), category("talents"), value.get("metadata", {}))
    return Database(raw["schema_version"], raw["generated_at"], raw["game_version"], raw["season_slug"], raw["source_mode"], specs)


def save_database(path: Path, database: Database) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(database.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def merge_lkg(new: Database, old: Database | None, settings: Settings, now: int | None = None) -> Database:
    timestamp = now or int(time.time())
    merged: dict[int, SpecResult] = {}
    for spec_id in sorted(set(new.specs) | set(old.specs if old else {})):
        incoming = new.specs.get(spec_id, SpecResult())
        previous = old.specs.get(spec_id, SpecResult()) if old else SpecResult()
        result = SpecResult(metadata=incoming.metadata or previous.metadata)
        for name in ("stats", "trinkets", "talents"):
            category = getattr(incoming, name) or getattr(previous, name)
            if category:
                age = (timestamp - category.generated_at) / 86400
                if age <= settings.hard_stale_days:
                    category.stale = age > settings.soft_stale_days
                    setattr(result, name, category)
        merged[spec_id] = result
    if not any(s.stats or s.trinkets or s.talents for s in merged.values()):
        raise ValueError("Refusing to publish an empty database")
    new.specs = merged
    return new

