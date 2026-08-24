local ES = EasyStats

function ES:IsTalentStringValid(code)
    return type(code) == "string" and #code >= 20 and #code <= 2048
        and code:match("^[A-Za-z0-9%+/%=_%-]+$") ~= nil
end

function ES:ShowTalentCopy(code)
    if not self.copyFrame then
        local frame = CreateFrame("Frame", "EasyStatsTalentCopyFrame", UIParent, "BackdropTemplate")
        frame:SetSize(520, 145); frame:SetPoint("CENTER"); frame:SetFrameStrata("DIALOG")
        frame:SetBackdrop({ bgFile = "Interface/Tooltips/UI-Tooltip-Background", edgeFile = "Interface/Tooltips/UI-Tooltip-Border", edgeSize = 12 })
        frame:SetBackdropColor(0.03, 0.05, 0.08, 0.98)
        local title = frame:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
        title:SetPoint("TOP", 0, -16); title:SetText(self.L.COPY)
        local edit = CreateFrame("EditBox", nil, frame, "InputBoxTemplate")
        edit:SetSize(470, 32); edit:SetPoint("CENTER", 0, 2); edit:SetAutoFocus(false)
        edit:SetScript("OnEscapePressed", function() frame:Hide() end)
        edit:SetScript("OnEditFocusGained", function(box) box:HighlightText() end)
        local close = CreateFrame("Button", nil, frame, "UIPanelCloseButton")
        close:SetPoint("TOPRIGHT", -4, -4)
        frame.edit = edit; self.copyFrame = frame
    end
    self.copyFrame.edit:SetText(code); self.copyFrame:Show(); self.copyFrame.edit:SetFocus(); self.copyFrame.edit:HighlightText()
end

function ES:OpenTalentUI()
    if PlayerSpellsUtil and PlayerSpellsUtil.OpenToClassSpecializationsTab then
        pcall(PlayerSpellsUtil.OpenToClassSpecializationsTab)
    elseif ToggleTalentFrame then
        pcall(ToggleTalentFrame)
    end
end

function ES:ApplyTalentBuild()
    local data = self.activeData and self.activeData.talents
    local code = data and data.importString
    if not self:IsTalentStringValid(code) then self:Print(self.L.IMPORT_FAILED); return end
    if InCombatLockdown and InCombatLockdown() then self:Print(self.L.LOCKED_COMBAT); return end
    local spec = self:GetActiveSpecialization()
    if not spec or spec.id ~= self.activeSpec.id then self:Print(self.L.IMPORT_FAILED); return end

    local attempted = false
    if C_ClassTalents and C_ClassTalents.ImportLoadout and C_ClassTalents.GetActiveConfigID then
        local configID = C_ClassTalents.GetActiveConfigID()
        if configID then
            attempted = true
            local ok, success = pcall(C_ClassTalents.ImportLoadout, configID, {}, "EasyStats - M+", code)
            if ok and success then
                self:Print(self.L.IMPORT_READY)
                self:OpenTalentUI()
                return
            end
            self:Debug("ImportLoadout rejected the import; using copy fallback")
        end
    end
    self:OpenTalentUI()
    self:ShowTalentCopy(code)
    self:Print(self.L.IMPORT_FAILED)
    if not attempted then self:Debug("ImportLoadout API not available") end
end

