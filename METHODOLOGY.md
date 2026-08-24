# Methodology

EasyStats processes the current Mythic+ season, all supported regions, timed runs from the previous 14 days, and characters at the current maximum level. It targets 150 unique characters per specialization (minimum 40, maximum 300). A character contributes at most once per specialization and UTC-day window.

The quality filter rejects untimed or stale runs, season/spec conflicts, invalid character levels, duplicate voters, and corrupt data. Categories are independent: missing talents do not discard usable stats or trinkets. An adaptive key-level percentile is lowered when necessary to retain the minimum sample for a less-represented specialization.

Observation weight combines key level above the adaptive threshold, recency, and snapshot quality. Stats normalize Crit, Haste, Mastery, and Versatility to shares, then use weighted medians. Adjacent values within 2.5 percentage points are displayed as approximately equal. This `metaStatPriority` is not an individual stat weight.

Trinkets are ranked by weighted unique-user adoption. Duplicate item IDs per player are counted once and known item-level variants map to a canonical item ID. The top four distinct IDs are emitted.

Talents are grouped by the normalized complete import string, never assembled node-by-node. The winner requires at least 40 valid voters and 15% weighted support. Complete strings include class, specialization, and hero-tree data as encoded by the game.

Stats, trinkets, and talents each have independent last-known-good values. A category becomes soft-stale after seven days and hard-stale after 30. Hard-stale data is not presented as current. Output replacement is transactional and refuses an empty database. Limitations include API field availability, profile snapshots that may post-date a run, survivorship bias in top runs, and the fact that popularity is not personalized optimization.

