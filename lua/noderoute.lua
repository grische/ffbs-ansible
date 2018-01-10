local json = require('luci.jsonc')
local popen = require('io').popen

local TABLE = 10
local TABLE_NAME = 'freifunk'
local RT_PROTO = 'freifunk'

function check_output(cmd)
    local f = assert(io.popen(cmd, 'r'))
    local s = assert(f:read('*a'))
    f:close()
    return s
end

function sleep(n)
    os.execute("sleep " .. tonumber(n))
end

function str_split(str, pattern)
    local res = {}
    for i in string.gmatch(str, pattern) do table.insert(res, i) end
    return res
end

function tablelength(T)
    local count = 0
    for _ in pairs(T) do count = count + 1 end
    return count
end

function has_value(tab, val)
    for index, value in ipairs(tab) do
        if value == val then
            return true
        end
    end
    return false
end


function dump(foo)
    print(json.stringify(foo))
end

function get_wg_info()
    -- done
    local output = check_output('wg show all dump')
    local results = {}
    for lineRaw in string.gmatch(output, "[^\n]+") do
        local line = str_split(lineRaw, "%S+")
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
            peer['allowed-ips'] = str_split(line[5], "[^,]+")
            peer['latest_handshake'] = tonumber(line[6])
            peer['transfer_rx'] = tonumber(line[7])
            peer['transfer_tx'] = tonumber(line[8])
            peer['presistent_keepalive'] = tonumber(line[8])
            results[line[1]]['peers'][line[2]] = peer
        end
    end
    return results
end

function get_handshake_ages()
    -- done
    local result = {}
    local now = os.time()
    local wg = get_wg_info()
    for iface, data in pairs(wg) do
        local peers = data['peers']
        if tablelength(peers) == 1 then
            for k,v in pairs(peers) do
                table.insert(result, {now - v['latest_handshake'], iface})
            end
        end
    end
    return result
end

function get_wg_links()
    -- done, not needed
    local output = check_output('ip a')
    local result = {}
    for i_raw in string.gmatch(output, "[0-9]+: wg-[^\n]+UP") do
        local sp = str_split(i_raw, '[^: ]+')
        local i = tonumber(sp[1])
        local name = sp[2]
        result[i] = name
        result[name] = i
    end
    return result
end

function get_wg_routes()
    -- done, test needed
    local result = {}
    local output = check_output('ip r show table '..TABLE)
    for line in string.gmatch(output, "[^\n]+") do
        if string.find(line, 'default via') then
            if string.find(line, 'proto '..RT_PROTO) then
                if not string.find(line, 'broadcast') then
                    for iface in string.gmatch(line, 'dev [a-z0-9-_]+') do
                        table.insert(result, iface:sub(5))
                    end
                end
            end
        end
    end
    return result
end

function set_wg_route(iface, id)
    -- done, test needed
    os.execute('ip r replace default via 10.0.0.'..id..' dev '..iface..' proto '..RT_PROTO..' table freifunk')
end

function update()
    -- done
    local active = {}
    for _, elem in ipairs(get_handshake_ages()) do
        if elem[1] < 180 then
            table.insert(active, elem[2])
        end
    end
    local current = get_wg_routes()
    assert(#current < 1, 'too many current routes')
    current = current[1]
    if current and has_value(active, current) then
        print('current route still active')
        return
    end
    if #active == 0 then
        print('no active tunnels')
        return
    end
    print('activating route for '..active[1])
    local id = tonumber(active[1]:match('[0-9]+'))
    set_wg_route(active[1], id)
end

function main()
    -- done
    while true do
        update()
        sleep(5)
    end
end

main()




