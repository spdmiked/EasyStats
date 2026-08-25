local ES = EasyStats

ES.lootSourceCache = ES.lootSourceCache or {}
ES.lootSourceCallbacks = ES.lootSourceCallbacks or {}
ES.lootSourceQueue = ES.lootSourceQueue or {}

local START_DELAY = 2
local STEP_DELAY = 0.04

local function loadEncounterJournal()
    if C_AddOns and C_AddOns.IsAddOnLoaded and C_AddOns.IsAddOnLoaded("Blizzard_EncounterJournal") then
        return true
    end
    local loader = C_AddOns and C_AddOns.LoadAddOn or UIParentLoadAddOn
    if not loader then return false end
    local ok = pcall(loader, "Blizzard_EncounterJournal")
    return ok and EJ_GetNumTiers and EJ_GetInstanceByIndex and EJ_GetNumLoot
end

local function lootInfo(index)
    if C_EncounterJournal and C_EncounterJournal.GetLootInfoByIndex then
        local info = C_EncounterJournal.GetLootInfoByIndex(index)
        if info then return info.itemID, info.encounterID end
    end
    if EJ_GetLootInfoByIndex then
        local _, _, _, _, itemID, _, encounterID = EJ_GetLootInfoByIndex(index)
        return itemID, encounterID
    end
end

function ES:PublishLootSource(itemID, source)
    self.lootSourceCache[itemID] = source
    if source ~= self.L.SOURCE_UNKNOWN and self.db and self.db.lootSources then
        self.db.lootSources[itemID] = source
    end
    local callbacks = self.lootSourceCallbacks[itemID] or {}
    self.lootSourceCallbacks[itemID] = nil
    for _, callback in ipairs(callbacks) do callback(source) end
end

function ES:ResolveLootSource(itemID, callback)
    local cached = self.lootSourceCache[itemID]
        or (self.db and self.db.lootSources and self.db.lootSources[itemID])
    if cached then
        self.lootSourceCache[itemID] = cached
        callback(cached)
        return
    end
    self.lootSourceCallbacks[itemID] = self.lootSourceCallbacks[itemID] or {}
    table.insert(self.lootSourceCallbacks[itemID], callback)
    if self.lootSourceScan then
        self.lootSourceScan.targets[itemID] = true
        return
    end
    self.lootSourceQueue[itemID] = true
    if self.lootSourceStartPending then return end
    self.lootSourceStartPending = true
    C_Timer.After(START_DELAY, function()
        ES.lootSourceStartPending = false
        ES:StartLootSourceScan()
    end)
end

function ES:StartLootSourceScan()
    if self.lootSourceScan then return end
    if not next(self.lootSourceQueue) then return end
    if InCombatLockdown and InCombatLockdown() then
        if not self.lootSourceStartPending then
            self.lootSourceStartPending = true
            C_Timer.After(START_DELAY, function()
                ES.lootSourceStartPending = false
                ES:StartLootSourceScan()
            end)
        end
        return
    end
    if not loadEncounterJournal() then
        local queued = self.lootSourceQueue
        self.lootSourceQueue = {}
        for itemID in pairs(queued) do self:PublishLootSource(itemID, self.L.SOURCE_UNKNOWN) end
        return
    end

    local originalTier = EJ_GetCurrentTier and EJ_GetCurrentTier()
    local originalDifficulty = EJ_GetDifficulty and EJ_GetDifficulty()
    local originalInstance = EJ_GetCurrentInstance and EJ_GetCurrentInstance()
    local _, _, classID = UnitClass("player")
    local spec = self:GetActiveSpecialization()
    if EJ_SetLootFilter then EJ_SetLootFilter(classID or 0, spec and spec.id or 0) end
    local targets = self.lootSourceQueue
    self.lootSourceQueue = {}
    self.lootSourceScan = {
        targets = targets, tier = EJ_GetNumTiers(), instance = 1,
        isRaid = false, originalTier = originalTier, originalDifficulty = originalDifficulty,
        originalInstance = originalInstance,
    }
    self:ContinueLootSourceScan()
end

function ES:HasPendingLootTargets(scan)
    scan = scan or self.lootSourceScan
    if not scan then return false end
    for itemID in pairs(scan.targets) do
        if not self.lootSourceCache[itemID] then return true end
    end
    return false
end

function ES:FinishLootSourceScan()
    local scan = self.lootSourceScan
    if not scan then return end
    for itemID in pairs(scan.targets) do
        if not self.lootSourceCache[itemID] then
            self:PublishLootSource(itemID, self.L.SOURCE_UNKNOWN)
        end
    end
    if EJ_ResetLootFilter then EJ_ResetLootFilter() end
    if scan.originalTier and EJ_SelectTier then EJ_SelectTier(scan.originalTier) end
    if scan.originalDifficulty and EJ_SetDifficulty then EJ_SetDifficulty(scan.originalDifficulty) end
    if scan.originalInstance and EJ_SelectInstance then EJ_SelectInstance(scan.originalInstance) end
    self.lootSourceScan = nil
end

function ES:ContinueLootSourceScan()
    local scan = self.lootSourceScan
    if not scan then return end
    if not self:HasPendingLootTargets(scan) then self:FinishLootSourceScan(); return end
    if EncounterJournal and EncounterJournal:IsShown() then
        C_Timer.After(1, function() ES:ContinueLootSourceScan() end)
        return
    end
    if scan.tier < 1 then self:FinishLootSourceScan(); return end
    EJ_SelectTier(scan.tier)
    local instanceID, instanceName = EJ_GetInstanceByIndex(scan.instance, scan.isRaid)
    if not instanceID then
        if not scan.isRaid then
            scan.isRaid, scan.instance = true, 1
        else
            scan.isRaid, scan.instance, scan.tier = false, 1, scan.tier - 1
        end
        C_Timer.After(STEP_DELAY, function() ES:ContinueLootSourceScan() end)
        return
    end

    EJ_SelectInstance(instanceID)
    for index = 1, (tonumber(EJ_GetNumLoot()) or 0) do
        local foundItemID, encounterID = lootInfo(index)
        if foundItemID and scan.targets[foundItemID] and not self.lootSourceCache[foundItemID] then
            local encounterName = encounterID and EJ_GetEncounterInfo and EJ_GetEncounterInfo(encounterID)
            local source = encounterName and (encounterName .. " (" .. instanceName .. ")") or instanceName
            self:PublishLootSource(foundItemID, source)
        end
    end
    if not self:HasPendingLootTargets(scan) then self:FinishLootSourceScan(); return end
    scan.instance = scan.instance + 1
    C_Timer.After(STEP_DELAY, function() ES:ContinueLootSourceScan() end)
end
