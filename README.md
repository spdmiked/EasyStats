# EasyStats

EasyStats is a lightweight, public World of Warcraft Retail **Midnight 12.1.0** addon for Mythic+. It detects the active specialization and shows an aggregated secondary-stat priority, the four most-used trinkets, and the most popular complete talent loadout from top timed runs.

These are population-level meta observations, not personalized SimulationCraft weights. EasyStats never connects to the internet from inside WoW. A separate Python pipeline uses documented Raider.IO and Blizzard Battle.net APIs, removes character identity after aggregation, and ships only anonymous recommendations in the addon update.

## Install the addon

Download the release ZIP, extract it, and place the `EasyStats` directory in `_retail_/Interface/AddOns/`. Restart WoW or reload the UI. Commands are `/easystats` and `/es`; run `/easystats help` for the command list.

## Run the data pipeline

Python 3.12 is required.

```bash
cd pipeline
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp ../.env.example ../.env
python -m specmeta_pipeline update --provider fixture --dry-run
DATA_PROVIDER=fixture python -m specmeta_pipeline update
```

For live updates set `BLIZZARD_CLIENT_ID`, `BLIZZARD_CLIENT_SECRET`, and optionally `RAIDERIO_API_KEY`, then run:

```bash
python -m specmeta_pipeline update --provider hybrid
python -m specmeta_pipeline validate
```

Create Blizzard client credentials in the Battle.net Developer Portal. Secrets are read only from environment variables and GitHub Secrets. Never add `.env` to version control.

## Test and package

```bash
cd pipeline
ruff check src tests
mypy src
pytest
cd ..
bash scripts/validate_package.sh
bash scripts/package_addon.sh
```

The ZIP is written to `dist/EasyStats-<version>.zip` with the required top-level `EasyStats/` directory. Scheduled data updates are separate from tagged public releases. Required repository secrets are `BLIZZARD_CLIENT_ID`, `BLIZZARD_CLIENT_SECRET`, and optionally `RAIDERIO_API_KEY`. CurseForge publishing additionally uses `CF_API_KEY`, `CF_PROJECT_ID`, and the numeric Midnight 12.1.0 `CF_GAME_VERSION_ID`; Wago uses `WAGO_API_TOKEN` when enabled. The release workflow refuses fixture data.

## Talent import safety

EasyStats attempts the current public `C_ClassTalents.ImportLoadout` API only out of combat and behind feature detection and `pcall`. If the client rejects or changes that API, EasyStats opens the native talent UI and displays a selectable import string. The player completes the native confirmation. The addon does not simulate clicks, bypass protected functions, or retry automatically after combat.

## AI disclosure

EasyStats was designed and initially implemented with assistance from OpenAI Codex. The maintainer is responsible for review, testing, releases, API compliance, and all published data. AI assistance does not imply affiliation with or endorsement by OpenAI, Blizzard Entertainment, Raider.IO, or CurseForge.

See [METHODOLOGY.md](METHODOLOGY.md), [DATA_SOURCES.md](DATA_SOURCES.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [CURSEFORGE_DESCRIPTION.md](CURSEFORGE_DESCRIPTION.md).
