local json = require('luci.jsonc')

local util = {}

function util.read_file(path)
    local file = io.open(path, "rb") -- r read mode and b binary mode
    if not file then return nil end
    local content = file:read "*a" -- *a or *all reads the whole file
    file:close()
    return content
end

function util.str_split(str, pattern)
    local res = {}
    for i in string.gmatch(str, pattern) do table.insert(res, i) end
    return res
end

function util.has_value(tab, val)
    for index, value in ipairs(tab) do
        if value == val then
            return true
        end
    end
    return false
end

function util.check_output(cmd)
    local f = assert(io.popen(cmd, 'r'))
    local s = assert(f:read('*a'))
    f:close()
    return s
end

function util.tablelength(T)
    local count = 0
    for _ in pairs(T) do count = count + 1 end
    return count
end

function util.nslookup(host)
    --TODO fix possible code injection
    local outp = util.check_output('grep '..host..' /etc/hosts')
    for ip in string.gmatch(outp, '[0-9.]+') do
        return ip
    end
    outp = util.check_output('nslookup '..host..' | grep "Address 1"')
    return util.str_split(outp, '[0-9.]+')[2]
end

function util.get_wg_info()
    local output = util.check_output('wg show all dump')
    local results = {}
    for lineRaw in string.gmatch(output, "[^\n]+") do
        local line = util.str_split(lineRaw, "%S+")
        if not results[line[1]] then
            local device = {}
            device['private_key'] = line[2]
            device['public_key'] = line[3]
            device['listen_port'] = tonumber(line[4])
            device['peers'] = {}
            results[line[1]] = device
        else
            local peer = {}
            if line[3] ~= "(none)" then
                peer['preshared_key'] = line[3]
            end
            peer['endpoint'] = line[4]
            peer['allowed-ips'] = util.str_split(line[5], "[^,]+")
            peer['latest_handshake'] = tonumber(line[6])
            peer['transfer_rx'] = tonumber(line[7])
            peer['transfer_tx'] = tonumber(line[8])
            peer['presistent_keepalive'] = tonumber(line[8])
            results[line[1]]['peers'][line[2]] = peer
        end
    end
    return results
end

return util

