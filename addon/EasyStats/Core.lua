local ES = EasyStats

function ES:GetActiveSpecialization()
    local index
    if C_SpecializationInfo and C_SpecializationInfo.GetSpecialization then
        index = C_SpecializationInfo.GetSpecialization()
    elseif GetSpecialization then
        index = GetSpecialization()
    end
    if not index then return nil end
    local id, name, _, icon
    if C_SpecializationInfo and C_SpecializationInfo.GetSpecializationInfo then
        id, name, _, icon = C_SpecializationInfo.GetSpecializationInfo(index)
    elseif GetSpecializationInfo then
        id, name, _, icon = GetSpecializationInfo(index)
    end
    if not id then return nil end
    return { id = id, name = name or tostring(id), icon = icon or 134400 }
end

function ES:Refresh()
    self.activeSpec = self:GetActiveSpecialization()
    if not self.activeSpec then
        if self.ui then self.ui:SetUnavailable(self.L.NO_DATA) end
        return
    end
    local data = self:GetSpecData(self.activeSpec.id)
    self.activeData = data
    if self.ui then self.ui:Render(self.activeSpec, data) end
end

function ES:ScheduleRefresh()
    if self.refreshPending then return end
    self.refreshPending = true
    C_Timer.After(0.15, function()
        ES.refreshPending = false
        ES:Refresh()
    end)
end
