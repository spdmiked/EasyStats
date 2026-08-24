# EasyStats — Mythic+ Meta at a Glance

EasyStats is a compact World of Warcraft Retail addon for **Midnight 12.1.0**. It automatically detects your current specialization and keeps the most useful Mythic+ meta information in a small movable panel:

- aggregated secondary-stat priority;
- four most-used trinkets, with native icons and item tooltips;
- the most popular complete Mythic+ talent loadout;
- freshness date and sample size;
- automatic refresh after a specialization change;
- collapsible 30×30 icon, saved position, scale, and lock state.

EasyStats is intentionally simple. It does not claim to replace SimulationCraft or a character-specific gear comparison. Recommendations summarize anonymized usage patterns from top timed Mythic+ runs.

## Safe by design

The addon never connects to external services from the game client and contains no API keys. Data is collected before release by an open-source Python pipeline using the documented [Raider.IO Developer API](https://raider.io/api) and Blizzard Battle.net APIs. Only aggregates are shipped; character names, realms, profile links, BattleTags, and raw profiles are excluded.

Talent application uses the public WoW API when available and permitted. If direct import is unavailable, EasyStats opens the native talent interface and provides a copyable code for player confirmation. It never bypasses combat lockdown or protected UI functions.

## Commands

`/easystats` or `/es` toggles the panel. Available commands: `show`, `hide`, `toggle`, `reset`, `lock`, `unlock`, `scale 0.8-1.5`, `debug`, and `version`.

## AI disclosure

EasyStats was designed and initially implemented with assistance from OpenAI Codex. Every public release, generated dataset, and compliance decision remains the responsibility of the project maintainer. The project is not affiliated with or endorsed by OpenAI, Blizzard Entertainment, Raider.IO, or CurseForge.
