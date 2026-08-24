from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Database


def write_report(root: Path, database: Database, changed: bool, errors: list[str] | None = None) -> None:
    payload: dict[str, Any] = {
        "generatedAt": database.generated_at, "sourceMode": database.source_mode,
        "season": database.season_slug, "changed": changed, "apiErrors": errors or [],
        "specs": {str(k): {
            name: getattr(v, name).sample_size if getattr(v, name) else 0
            for name in ("stats", "trinkets", "talents")
        } for k, v in database.specs.items()},
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "latest-update.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# EasyStats update report", "", f"- Source: {database.source_mode}",
             f"- Season: {database.season_slug}", f"- Generated: {database.generated_at}",
             f"- Lua changed: {changed}", "", "| specID | stats | trinkets | talents |", "|---:|---:|---:|---:|"]
    for key, samples in payload["specs"].items():
        lines.append(f"| {key} | {samples['stats']} | {samples['trinkets']} | {samples['talents']} |")
    (root / "latest-update.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

