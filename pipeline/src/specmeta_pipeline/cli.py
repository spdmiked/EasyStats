from __future__ import annotations

import argparse
import asyncio
import time
from dataclasses import replace
from pathlib import Path

from .aggregation import aggregate_by_spec, prepare_observations
from .config import DEFAULT_OUTPUT, DEFAULT_REPORTS, DEFAULT_STATE, RETAIL_SPEC_IDS, Settings
from .fixtures import sample_observations
from .lua import render, validate_text, write_atomic
from .models import Database
from .pipeline import collect_live
from .report import write_report
from .state import load_database, merge_lkg, save_database


def build_fixture_database(settings: Settings) -> Database:
    now = int(time.time())
    rows = prepare_observations(sample_observations(), settings, "fixture-season")
    return Database(1, now, "fixture", "fixture-season", "fixture", aggregate_by_spec(rows, settings, now))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="easystats-pipeline")
    sub = result.add_subparsers(dest="command", required=True)
    update = sub.add_parser("update")
    update.add_argument("--provider", choices=("hybrid", "raiderio", "blizzard", "fixture"))
    update.add_argument("--dry-run", action="store_true")
    validate = sub.add_parser("validate")
    validate.add_argument("--production", action="store_true")
    sub.add_parser("generate-lua")
    sub.add_parser("report")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    settings = Settings.from_env()
    if getattr(args, "provider", None):
        settings = replace(settings, provider=args.provider)
    if args.command == "validate":
        text = DEFAULT_OUTPUT.read_text(encoding="utf-8")
        validate_text(text)
        if args.production and 'sourceMode = "fixture"' in text:
            raise SystemExit("Refusing to release fixture data")
        if args.production:
            database = load_database(DEFAULT_STATE)
            if database is None:
                raise SystemExit("Refusing to release without pipeline state")
            missing = []
            for spec_id in RETAIL_SPEC_IDS:
                spec = database.specs.get(spec_id)
                for name in ("stats", "trinkets", "talents"):
                    category = getattr(spec, name, None) if spec else None
                    minimum = settings.min_talent_sample if name == "talents" else settings.min_per_spec
                    if category is None or category.sample_size < minimum:
                        missing.append(f"{spec_id}:{name}")
                if spec and spec.trinkets and len(spec.trinkets.value.get("items", [])) != 4:
                    missing.append(f"{spec_id}:trinkets-not-four")
            if missing:
                raise SystemExit(
                    "Refusing to release incomplete live data: " + ", ".join(missing)
                )
        return 0
    errors: list[str] = []
    if settings.provider == "fixture":
        database = build_fixture_database(settings)
    else:
        season, rows, errors = asyncio.run(collect_live(settings, Path(".cache/specmeta")))
        now = int(time.time())
        prepared = prepare_observations(rows, settings, season)
        database = Database(1, now, "retail", season, settings.provider,
                            aggregate_by_spec(prepared, settings, now))
    old = load_database(DEFAULT_STATE)
    database = merge_lkg(database, old, settings)
    if args.command == "generate-lua":
        write_atomic(DEFAULT_OUTPUT, database)
        return 0
    if args.command == "report":
        write_report(DEFAULT_REPORTS, database, False)
        return 0
    if getattr(args, "dry_run", False):
        print(render(database))
        return 0
    changed = write_atomic(DEFAULT_OUTPUT, database)
    save_database(DEFAULT_STATE, database)
    write_report(DEFAULT_REPORTS, database, changed, errors)
    return 0
