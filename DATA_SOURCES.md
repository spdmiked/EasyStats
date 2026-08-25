# Data sources and retention

EasyStats does not parse rendered HTML or browser UI elements.

## Raider.IO public specialization leaderboards

Candidate characters are selected from the public specialization leaderboard data
used by Raider.IO's official ranking pages. This is necessary to select every class
specialization directly instead of inferring a specialization from an overall run
ranking. The pipeline validates the returned numeric Blizzard specialization ID and
rejects mismatched rows. Character identifiers and raw leaderboard responses remain
temporary cache inputs and are never shipped with the addon.

## Raider.IO Developer API

The documented Raider.IO Developer API supplies current-season and fallback run
context. It is also used when a newly added specialization is not yet correctly
filtered by the public specialization leaderboard. An API key is optional where the
documented endpoint allows anonymous use. Disable it with `DATA_PROVIDER=blizzard`.

## Blizzard Battle.net API

The Blizzard provider uses OAuth Client Credentials and official game-data/profile APIs for season, specialization, item, equipment, and loadout validation. It supports EU, US, KR, and TW. Disable it with `DATA_PROVIDER=raiderio`.

`DATA_PROVIDER=hybrid` is the default. Raider.IO discovers run context; Blizzard validates or supplies an official fallback where its documented APIs provide equivalent information. A fallback that cannot reach the configured minimum sample is rejected.

Responses are cached on disk with a default six-hour TTL. Cache keys are hashed, secrets are never written to cache, and cache contents are excluded from releases. Raw responses and character references are temporary pipeline inputs. After aggregation, only stat shares, four item IDs with usage rates and strongest observed item variants, one complete talent code, sample counts, timestamps, and method/source identifiers remain. Cache retention must be adjusted if provider terms require a shorter period.

Users and distributors must review current Blizzard and Raider.IO API terms and attribution requirements before operating or redistributing live datasets.
