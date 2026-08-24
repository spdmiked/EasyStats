local ES = EasyStats

ES.itemCallbacks = {}

function ES:LoadItem(itemID, callback)
    if type(itemID) ~= "number" or itemID <= 0 then return end
    if C_Item and C_Item.GetItemInfo then
        local info = C_Item.GetItemInfo(itemID)
        if info and info.itemName then callback(info.itemName, info.iconFileID, info.hyperlink); return end
    end
    local name, link, _, _, _, _, _, _, _, icon = GetItemInfo(itemID)
    if name then callback(name, icon, link); return end
    self.itemCallbacks[itemID] = self.itemCallbacks[itemID] or {}
    table.insert(self.itemCallbacks[itemID], callback)
    if C_Item and C_Item.RequestLoadItemDataByID then C_Item.RequestLoadItemDataByID(itemID) end
end

function ES:OnItemLoaded(itemID, success)
    local callbacks = self.itemCallbacks[itemID]
    if not callbacks then return end
    self.itemCallbacks[itemID] = nil
    if not success then return end
    for _, callback in ipairs(callbacks) do self:LoadItem(itemID, callback) end
end

