local ES = EasyStats

local function resetPosition()
    local p = ES.db.profile
    for key, value in pairs(ES.defaults.profile) do p[key] = value end
    ES.ui.frame:ClearAllPoints(); ES.ui.frame:SetPoint(p.point, UIParent, p.relativePoint, p.x, p.y); ES.ui.frame:SetScale(p.scale)
    ES:SetCollapsed(false); ES:Print(ES.L.RESET)
end

function ES:Slash(input)
    local command, argument = input:lower():match("^(%S*)%s*(.-)$")
    if command == "show" then self:SetCollapsed(false); self.ui.frame:Show()
    elseif command == "hide" then self.ui.frame:Hide(); self.ui.mini:Hide()
    elseif command == "toggle" or command == "" then self:SetCollapsed(not self.db.profile.collapsed)
    elseif command == "reset" then resetPosition()
    elseif command == "lock" then self.db.profile.locked = true; self:Print(self.L.LOCKED)
    elseif command == "unlock" then self.db.profile.locked = false; self:Print(self.L.UNLOCKED)
    elseif command == "scale" then
        local scale = tonumber(argument)
        if scale and scale >= 0.8 and scale <= 1.5 then self.db.profile.scale = scale; self.ui.frame:SetScale(scale); self.ui.mini:SetScale(scale) else self:Print(self.L.HELP) end
    elseif command == "debug" then self.debugEnabled = not self.debugEnabled; self:Print("Debug: " .. tostring(self.debugEnabled))
    elseif command == "version" then self:Print(string.format(self.L.VERSION, self.version))
    else self:Print(self.L.HELP) end
end

SLASH_EASYSTATS1 = "/easystats"
SLASH_EASYSTATS2 = "/es"
SlashCmdList.EASYSTATS = function(input) ES:Slash(input or "") end

