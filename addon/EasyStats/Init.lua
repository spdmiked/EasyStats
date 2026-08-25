EasyStats = EasyStats or {}
local ES = EasyStats
ES.name = "EasyStats"
ES.version = "1.0.1"
ES.schemaVersion = 1
ES.debugEnabled = false

local locale = GetLocale and GetLocale() or "enUS"
ES.L = EasyStats_Locales[locale] or EasyStats_Locales.enUS

ES.defaults = {
    schemaVersion = 1,
    profile = { point = "TOPRIGHT", relativePoint = "TOPRIGHT", x = -40, y = -220,
        scale = 1.0, collapsed = false, locked = false, showSampleSize = false },
}

function ES:Print(message)
    if DEFAULT_CHAT_FRAME then DEFAULT_CHAT_FRAME:AddMessage("|cff55c7ffEasyStats:|r " .. tostring(message)) end
end

function ES:Debug(message)
    if self.debugEnabled then self:Print("[debug] " .. tostring(message)) end
end

function ES:MigrateSettings(saved)
    if type(saved) ~= "table" then saved = {} end
    if type(saved.profile) ~= "table" then saved.profile = {} end
    for key, value in pairs(self.defaults.profile) do
        if saved.profile[key] == nil then saved.profile[key] = value end
    end
    saved.schemaVersion = self.schemaVersion
    return saved
end

function ES:InitializeSettings()
    EasyStatsDB = self:MigrateSettings(EasyStatsDB)
    self.db = EasyStatsDB
end
