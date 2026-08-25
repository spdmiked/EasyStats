local ES = EasyStats
local events = CreateFrame("Frame")
events:RegisterEvent("ADDON_LOADED")
events:RegisterEvent("PLAYER_ENTERING_WORLD")
events:RegisterEvent("PLAYER_SPECIALIZATION_CHANGED")
events:RegisterEvent("ITEM_DATA_LOAD_RESULT")

events:SetScript("OnEvent", function(_, event, ...)
    if event == "ADDON_LOADED" then
        local addonName = ...
        if addonName ~= "EasyStats" then return end
        ES:InitializeSettings(); ES:CreateUI()
    elseif event == "ITEM_DATA_LOAD_RESULT" then
        ES:OnItemLoaded(...)
    elseif event == "PLAYER_SPECIALIZATION_CHANGED" then
        local unit = ...; if unit == "player" then ES:ScheduleRefresh() end
    elseif event == "PLAYER_ENTERING_WORLD" then
        ES:ScheduleRefresh()
    end
end)
