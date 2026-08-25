# Changelog

## 1.0.1 — 2026-08-25

### Fixed

- Collects targeted samples for every Retail specialization instead of allowing rare specs to ship empty.
- Keeps the active specialization name and icon visible when a category is unavailable.
- Uses the native Blizzard talent import flow with a pre-filled import-dialog fallback.
- Shows the strongest observed item variant in trinket tooltips instead of the base-level item.
- Adds boss and dungeon or raid source information below every trinket.
- Replaces the poorly cropped project icon and rewrites the CurseForge description for players.

### Validation

- Production releases now fail if any Retail specialization lacks stats, four trinkets, or a valid talent sample.

## 1.0.0 — 2026-08-24

### Code

- Initial Midnight 12.1.0 addon, data pipeline, tests, packaging, and release automation.

### Data

- Development builds include fixture-only data; public releases require a successful live pipeline update.

### Methodology

- Added adaptive sampling, weighted medians, complete-loadout voting, and category-level last-known-good protection.
