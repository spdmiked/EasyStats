local ES = EasyStats

local function tooltip(owner, title, body, category)
    GameTooltip:SetOwner(owner, "ANCHOR_RIGHT")
    GameTooltip:SetText(title, 0.35, 0.8, 1)
    GameTooltip:AddLine(body, 1, 1, 1, true)
    if category then
        GameTooltip:AddLine(" ")
        GameTooltip:AddDoubleLine(ES.L.DATA, ES:FormatDate(category.generatedAt))
        GameTooltip:AddDoubleLine(ES.L.SAMPLE, tostring(category.sampleSize or 0) .. " " .. ES.L.PLAYERS)
        GameTooltip:AddLine(ES:FreshnessText(category), category._softStale and 1 or 0.4, category._softStale and 0.8 or 1, 0.3)
    end
    GameTooltip:Show()
end

local function sectionLabel(parent, text, y)
    local label = parent:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    label:SetPoint("TOPLEFT", 16, y); label:SetText(text); label:SetTextColor(0.35, 0.8, 1)
    return label
end

function ES:SavePosition(frame)
    local point, _, relativePoint, x, y = frame:GetPoint(1)
    self.db.profile.point, self.db.profile.relativePoint = point, relativePoint
    self.db.profile.x, self.db.profile.y = x, y
    if self.ui then
        local counterpart = frame == self.ui.frame and self.ui.mini or self.ui.frame
        counterpart:ClearAllPoints()
        counterpart:SetPoint(point, UIParent, relativePoint, x, y)
    end
end

function ES:SetCollapsed(collapsed)
    self.db.profile.collapsed = collapsed
    self.ui.frame:SetShown(not collapsed); self.ui.mini:SetShown(collapsed)
end

function ES:CreateUI()
    local frame = CreateFrame("Frame", "EasyStatsFrame", UIParent, "BackdropTemplate")
    frame:SetSize(380, 403); frame:SetMovable(true); frame:EnableMouse(true); frame:SetClampedToScreen(true)
    frame:SetBackdrop({ bgFile = "Interface/Tooltips/UI-Tooltip-Background", edgeFile = "Interface/Tooltips/UI-Tooltip-Border", edgeSize = 12 })
    frame:SetBackdropColor(0.025, 0.04, 0.065, 0.94); frame:SetBackdropBorderColor(0.72, 0.60, 0.32, 1); frame:SetScale(self.db.profile.scale)
    frame:SetPoint(self.db.profile.point, UIParent, self.db.profile.relativePoint, self.db.profile.x, self.db.profile.y)
    frame:RegisterForDrag("LeftButton")
    frame:SetScript("OnDragStart", function(f) if not ES.db.profile.locked then f:StartMoving() end end)
    frame:SetScript("OnDragStop", function(f) f:StopMovingOrSizing(); ES:SavePosition(f) end)

    local icon = frame:CreateTexture(nil, "ARTWORK"); icon:SetSize(34, 34); icon:SetPoint("TOPLEFT", 16, -11)
    local title = frame:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge"); title:SetPoint("LEFT", icon, "RIGHT", 10, 0); title:SetJustifyH("LEFT")
    local brand = frame:CreateFontString(nil, "OVERLAY", "GameFontNormal"); brand:SetPoint("LEFT", title, "RIGHT", 8, 0); brand:SetText(self.L.HEADER_SUFFIX); brand:SetTextColor(0.35, 0.8, 1)
    local eye = CreateFrame("Button", nil, frame); eye:SetSize(24, 24); eye:SetPoint("TOPRIGHT", -8, -9)
    eye:SetNormalTexture("Interface/Buttons/UI-Panel-HideButton-Up"); eye:SetScript("OnClick", function() ES:SetCollapsed(true) end)

    local divider = frame:CreateTexture(nil, "ARTWORK"); divider:SetColorTexture(0.22, 0.27, 0.31, 0.65); divider:SetSize(348, 1); divider:SetPoint("TOPLEFT", 16, -48)

    local statsLabel = sectionLabel(frame, self.L.STATS, -62)
    local stats = frame:CreateFontString(nil, "OVERLAY", "GameFontHighlight"); stats:SetPoint("TOPLEFT", 16, -82); stats:SetWidth(348); stats:SetJustifyH("LEFT")
    statsLabel:SetScript("OnEnter", function(owner) tooltip(owner, ES.L.STATS, ES.L.META_TOOLTIP, ES.activeData and ES.activeData.stats) end)
    statsLabel:SetScript("OnLeave", GameTooltip_Hide); statsLabel:EnableMouse(true)

    local trinketLabel = sectionLabel(frame, self.L.TRINKETS, -116); trinketLabel:EnableMouse(true)
    trinketLabel:SetScript("OnEnter", function(owner) tooltip(owner, ES.L.TRINKETS, ES.L.TRINKET_TOOLTIP, ES.activeData and ES.activeData.trinkets) end)
    trinketLabel:SetScript("OnLeave", GameTooltip_Hide)
    local rows = {}
    for index = 1, 4 do
        local row = CreateFrame("Button", nil, frame); row:SetSize(348, 52); row:SetPoint("TOPLEFT", 16, -137 - (index - 1) * 54)
        local rank = row:CreateFontString(nil, "OVERLAY", "GameFontHighlight"); rank:SetPoint("TOPLEFT", 0, -5); rank:SetText(index .. ".")
        local itemIcon = row:CreateTexture(nil, "ARTWORK"); itemIcon:SetSize(34, 34); itemIcon:SetPoint("TOPLEFT", 24, -1)
        local name = row:CreateFontString(nil, "OVERLAY", "GameFontHighlight"); name:SetPoint("TOPLEFT", itemIcon, "TOPRIGHT", 8, -1); name:SetWidth(282); name:SetJustifyH("LEFT")
        local source = row:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall"); source:SetPoint("TOPLEFT", name, "BOTTOMLEFT", 0, -2); source:SetWidth(282); source:SetJustifyH("LEFT"); source:SetJustifyV("TOP")
        row.icon, row.name, row.source = itemIcon, name, source
        row:SetScript("OnEnter", function(r)
            if r.itemID then GameTooltip:SetOwner(r, "ANCHOR_RIGHT")
                local ok = pcall(GameTooltip.SetHyperlink, GameTooltip, r.itemLink or ("item:" .. r.itemID))
                if not ok then GameTooltip:SetItemByID(r.itemID) end
                if r.usage then GameTooltip:AddLine(string.format("Usage: %d%%", r.usage * 100), 0.35, 0.8, 1) end GameTooltip:Show() end
        end)
        row:SetScript("OnLeave", GameTooltip_Hide)
        row:SetScript("OnClick", function(r) if r.link and ChatEdit_InsertLink then ChatEdit_InsertLink(r.link) end end)
        rows[index] = row
    end

    local talentLabel = sectionLabel(frame, self.L.TALENTS, -351); talentLabel:EnableMouse(true)
    talentLabel:SetScript("OnEnter", function(owner) tooltip(owner, ES.L.TALENTS, ES.L.TALENT_TOOLTIP, ES.activeData and ES.activeData.talents) end)
    talentLabel:SetScript("OnLeave", GameTooltip_Hide)
    local support = frame:CreateFontString(nil, "OVERLAY", "GameFontHighlight"); support:SetPoint("TOPLEFT", 16, -371)
    local apply = CreateFrame("Button", nil, frame, "UIPanelButtonTemplate"); apply:SetSize(112, 24); apply:SetPoint("BOTTOMRIGHT", -12, 11); apply:SetText(self.L.APPLY)
    apply:SetScript("OnClick", function() ES:ApplyTalentBuild() end)

    local mini = CreateFrame("Button", "EasyStatsMiniButton", UIParent, "BackdropTemplate")
    mini:SetSize(30, 30); mini:SetMovable(true); mini:EnableMouse(true); mini:RegisterForDrag("LeftButton"); mini:SetClampedToScreen(true)
    mini:SetScale(self.db.profile.scale)
    mini:SetBackdrop({ bgFile = "Interface/Tooltips/UI-Tooltip-Background", edgeFile = "Interface/Tooltips/UI-Tooltip-Border", edgeSize = 10 }); mini:SetBackdropColor(0.02, 0.04, 0.08, 0.95)
    mini:SetPoint(self.db.profile.point, UIParent, self.db.profile.relativePoint, self.db.profile.x, self.db.profile.y)
    local miniIcon = mini:CreateTexture(nil, "ARTWORK"); miniIcon:SetAllPoints(); mini.icon = miniIcon
    mini:SetScript("OnClick", function() ES:SetCollapsed(false) end)
    mini:SetScript("OnDragStart", function(f) if not ES.db.profile.locked then f:StartMoving() end end)
    mini:SetScript("OnDragStop", function(f) f:StopMovingOrSizing(); ES:SavePosition(f); frame:ClearAllPoints(); frame:SetPoint(ES.db.profile.point, UIParent, ES.db.profile.relativePoint, ES.db.profile.x, ES.db.profile.y) end)
    mini:SetScript("OnEnter", function(owner) GameTooltip:SetOwner(owner, "ANCHOR_RIGHT"); GameTooltip:SetText(ES.L.SHOW); GameTooltip:Show() end)
    mini:SetScript("OnLeave", GameTooltip_Hide)

    local ui = { frame = frame, mini = mini, icon = icon, title = title, brand = brand, stats = stats, rows = rows, support = support, apply = apply }
    function ui:SetUnavailable(message, preserveHeader)
        if not preserveHeader then self.title:SetText(ES.L.ADDON_NAME); self.brand:SetText(ES.L.HEADER_FALLBACK); self.icon:SetTexture(134400) end
        self.stats:SetText(message); self.support:SetText(message); self.apply:Disable()
        for _, row in ipairs(self.rows) do row.name:SetText("—"); row.source:SetText(""); row.icon:SetTexture(nil); row.itemID = nil; row.itemLink = nil end
    end
    function ui:Render(spec, data)
        self.title:SetText(spec.name); self.brand:SetText(ES.L.HEADER_SUFFIX); self.icon:SetTexture(spec.icon); self.mini.icon:SetTexture(spec.icon)
        if not data then self:SetUnavailable(ES.L.NO_DATA, true); return end
        self.stats:SetText(data.stats and not data.stats._hardStale and ES:FormatStats(data.stats) or ES.L.NO_DATA)
        for index, row in ipairs(self.rows) do
            local item = data.trinkets and not data.trinkets._hardStale and data.trinkets.items and data.trinkets.items[index]
            row.itemID, row.usage, row.link = item and item.itemID, item and item.usage, nil
            row.itemLink = item and ES:BuildItemLink(item) or nil
            row.icon:SetTexture(134400); row.name:SetText(item and ES.L.LOADING_ITEM or "—")
            row.source:SetText(item and ES.L.SOURCE_LOADING or "")
            if item then ES:LoadItem(item.itemID, function(name, texture, link)
                if row.itemID == item.itemID then row.name:SetText(name); row.icon:SetTexture(texture); row.link = row.itemLink or link end
            end); ES:ResolveLootSource(item.itemID, function(source)
                if row.itemID == item.itemID then row.source:SetText(string.format(ES.L.SOURCE_FORMAT, source)) end
            end) end
        end
        if data.talents and not data.talents._hardStale then
            self.support:SetText(string.format(ES.L.BUILD_SUPPORT, math.floor((data.talents.support or 0) * 100 + 0.5))); self.apply:Enable()
        else self.support:SetText(ES.L.NO_DATA); self.apply:Disable() end
    end
    self.ui = ui
    self:SetCollapsed(self.db.profile.collapsed)
end
