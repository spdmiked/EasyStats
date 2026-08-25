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
    if not PlayerSpellsFrame then
        local loader = C_AddOns and C_AddOns.LoadAddOn or UIParentLoadAddOn
        if loader then pcall(loader, "Blizzard_PlayerSpells") end
    end
    if PlayerSpellsUtil and (PlayerSpellsUtil.OpenToClassTalentsTab or PlayerSpellsUtil.OpenToClassSpecializationsTab) then
        local open = PlayerSpellsUtil.OpenToClassTalentsTab or PlayerSpellsUtil.OpenToClassSpecializationsTab
        pcall(open)
    elseif ToggleTalentFrame then
        pcall(ToggleTalentFrame)
    end
end

function ES:OpenNativeTalentImport(code)
    self:OpenTalentUI()
    local dialog = ClassTalentLoadoutImportDialog
    if not dialog or not dialog.ShowDialog then return false end
    local ok = pcall(dialog.ShowDialog, dialog)
    if not ok then return false end
    local importBox = dialog.ImportControl and dialog.ImportControl.InputContainer
        and dialog.ImportControl.InputContainer.EditBox
    local nameBox = dialog.NameControl and dialog.NameControl.EditBox
    if not importBox then return false end
    importBox:SetText(code)
    if nameBox then nameBox:SetText("EasyStats - M+") end
    return true
end

function ES:ApplyTalentBuild()
    local data = self.activeData and self.activeData.talents
    local code = data and data.importString
    if not self:IsTalentStringValid(code) then self:Print(self.L.IMPORT_FAILED); return end
    if InCombatLockdown and InCombatLockdown() then self:Print(self.L.LOCKED_COMBAT); return end
    local spec = self:GetActiveSpecialization()
    if not spec or spec.id ~= self.activeSpec.id then self:Print(self.L.IMPORT_FAILED); return end

    self:OpenTalentUI()
    local talentFrame = PlayerSpellsFrame and PlayerSpellsFrame.TalentsFrame
    if talentFrame and talentFrame.ImportLoadout then
        local ok, success = pcall(talentFrame.ImportLoadout, talentFrame, code, "EasyStats - M+")
        if ok and success ~= false then
            self:Print(self.L.IMPORT_READY)
            return
        end
        self:Debug("Native talent frame rejected the direct import")
    end
    if self:OpenNativeTalentImport(code) then
        self:Print(self.L.IMPORT_READY)
        return
    end
    self:ShowTalentCopy(code)
    self:Print(self.L.IMPORT_FAILED)
    self:Debug("Native talent importer was unavailable; using copy fallback")
end
