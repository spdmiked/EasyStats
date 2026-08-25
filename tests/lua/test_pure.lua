GetLocale = function() return "enUS" end
GetServerTime = function() return 1787529600 end
time = os.time
date = os.date
DEFAULT_CHAT_FRAME = { AddMessage = function() end }

dofile("addon/EasyStats/Localization/enUS.lua")
dofile("addon/EasyStats/Init.lua")
dofile("addon/EasyStats/DataAccess.lua")
dofile("addon/EasyStats/Talents.lua")
dofile("addon/EasyStats/ItemLoader.lua")
dofile("addon/EasyStats/LootSource.lua")

local ES = EasyStats
local migrated = ES:MigrateSettings({})
assert(migrated.schemaVersion == 1)
assert(migrated.profile.scale == 1.0)
assert(type(migrated.lootSources) == "table")
assert(ES:IsTalentStringValid("BAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"))
assert(not ES:IsTalentStringValid("bad string"))
assert(ES:FormatStats({ order = { "HASTE", "MASTERY" }, separators = { "≈" } }) == "Haste ≈ Mastery")

local requested
local loaded = false
C_Item = {
    GetItemInfo = function(itemID)
        if loaded then return { itemName = "Fixture Trinket", iconFileID = 123, hyperlink = "item:" .. itemID } end
    end,
    RequestLoadItemDataByID = function(itemID) requested = itemID end,
}
GetItemInfo = function() return nil end
local received
ES:LoadItem(100001, function(name) received = name end)
assert(requested == 100001 and received == nil)
loaded = true
ES:OnItemLoaded(100001, true)
assert(received == "Fixture Trinket")
assert(ES:BuildItemLink({ itemID = 250144, bonuses = { 13440, 12806 } }) ==
    "item:250144::::::::::::2:13440:12806")

ES.db = { lootSources = {} }
ES.lootSourceCache = {}
ES.lootSourceCallbacks = {}
ES:PublishLootSource(250144, "Emberdawn (The Dreamrift)")
assert(ES.db.lootSources[250144] == "Emberdawn (The Dreamrift)")
local scan = { targets = { [250144] = true, [250145] = true } }
assert(ES:HasPendingLootTargets(scan))
ES.lootSourceCache[250145] = "Boss (Raid)"
assert(not ES:HasPendingLootTargets(scan))

EasyStatsGeneratedDB = { schemaVersion = 1, contexts = { mythicplus = { [253] = {
    stats = { generatedAt = 1787529600 }, trinkets = { generatedAt = 1787529600 }, talents = { generatedAt = 1787529600 },
} } } }
local data = ES:GetSpecData(253, 1787529600)
assert(data ~= nil)
local missing = ES:GetSpecData(999, 1787529600)
assert(missing == nil)
local stale = ES:GetSpecData(253, 1787529600 + 31 * 86400)
assert(stale == nil)

local printed
ES.Print = function(_, message) printed = message end
ES.activeData = { talents = { importString = "BAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" } }
ES.activeSpec = { id = 253 }
ES.GetActiveSpecialization = function() return { id = 253 } end
InCombatLockdown = function() return true end
ES:ApplyTalentBuild()
assert(printed == ES.L.LOCKED_COMBAT)
print("Lua pure-function tests passed")
