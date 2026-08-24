local ES = EasyStats

function ES:GetSpecData(specID, now)
    local db = EasyStatsGeneratedDB
    if type(db) ~= "table" or db.schemaVersion ~= 1 then return nil, "invalid-schema" end
    local context = db.contexts and db.contexts.mythicplus
    local data = context and context[specID]
    if not data then return nil, "missing" end
    now = now or (GetServerTime and GetServerTime()) or time()
    local usable = false
    for _, key in ipairs({ "stats", "trinkets", "talents" }) do
        local category = data[key]
        if category and type(category.generatedAt) == "number" then
            local age = now - category.generatedAt
            category._hardStale = age > 30 * 86400
            category._softStale = category.stale or age > 7 * 86400
            if not category._hardStale then usable = true end
        end
    end
    return usable and data or nil, usable and nil or "hard-stale"
end

function ES:FormatStats(stats)
    if not stats or type(stats.order) ~= "table" then return self.L.NO_DATA end
    local output = {}
    for index, key in ipairs(stats.order) do
        output[#output + 1] = self.L[key] or key
        if stats.separators and stats.separators[index] then output[#output + 1] = stats.separators[index] end
    end
    return table.concat(output, " ")
end

function ES:FormatDate(timestamp)
    if not timestamp then return "—" end
    return date("%d.%m.%Y", timestamp)
end

function ES:FreshnessText(category)
    return category and category._softStale and self.L.STALE or self.L.FRESH
end

