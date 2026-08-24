# EasyStats architecture

EasyStats has two security boundaries. The Python 3.12 pipeline is the only component that can use the network. It discovers timed Mythic+ runs through documented APIs, validates observations, removes character identity, aggregates each specialization, and atomically emits `GeneratedData.lua`. The Lua addon only reads those aggregates.

The pipeline is split into providers, immutable input models, quality filtering, three independent aggregators, category-level last-known-good state, a deterministic Lua serializer, and reporting. `hybrid` uses Raider.IO for discovery and Blizzard for official validation/fallback. A failed category retains its previous valid value without blocking successful categories. An empty result can never replace production data.

The addon separates pure data access and formatting from WoW API adapters. Events are debounced. Item information is requested asynchronously from the game cache. Talent import uses feature detection and `pcall`; when the public API cannot safely complete the import, a native-window plus copy dialog leaves confirmation to the player.

