# Data sources and retention

EasyStats uses only documented APIs; it does not scrape HTML.

## Raider.IO Developer API

The Raider.IO provider discovers top timed Mythic+ runs and reads the available roster, specialization, equipment, and talent snapshot fields. An API key is optional where the documented endpoint allows anonymous use. Disable it with `DATA_PROVIDER=blizzard`.

## Blizzard Battle.net API

The Blizzard provider uses OAuth Client Credentials and official game-data/profile APIs for season, specialization, item, equipment, and loadout validation. It supports EU, US, KR, and TW. Disable it with `DATA_PROVIDER=raiderio`.

`DATA_PROVIDER=hybrid` is the default. Raider.IO discovers run context; Blizzard validates or supplies an official fallback where its documented APIs provide equivalent information. A fallback that cannot reach the configured minimum sample is rejected.

Responses are cached on disk with a default six-hour TTL. Cache keys are hashed, secrets are never written to cache, and cache contents are excluded from releases. Raw responses and character references are temporary pipeline inputs. After aggregation, only stat shares, four item IDs and usage rates, one complete talent code, sample counts, timestamps, and method/source identifiers remain. Cache retention must be adjusted if provider terms require a shorter period.

Users and distributors must review current Blizzard and Raider.IO API terms and attribution requirements before operating or redistributing live datasets.

