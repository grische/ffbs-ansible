local json = require('luci.jsonc')
local util = require('util')

local TABLE = 10
local TABLE_NAME = 'freifunk'
local RT_PROTO = 'freifunk'

function sleep(n)
    os.execute("sleep " .. tonumber(n))
end

function dump(foo)
    print(json.stringify(foo))
end

function get_wg_info()
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

function get_handshake_ages()
    local result = {}
    local now = os.time()
    local wg = get_wg_info()
    for iface, data in pairs(wg) do
        local peers = data['peers']
        if util.tablelength(peers) == 1 then
            for k,v in pairs(peers) do
                table.insert(result, {now - v['latest_handshake'], iface})
            end
        end
    end
    return result
end

function get_wg_routes()
    local result = {}
    local output = util.check_output('ip r show table '..TABLE)
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
    return os.execute('ip r replace default via 10.0.0.'..id..' dev '..iface..' proto '..RT_PROTO..' table freifunk')
end

function update()
    local active = {}
    for _, elem in ipairs(get_handshake_ages()) do
        if elem[1] < 180 then
            table.insert(active, elem[2])
        end
    end
    local current = get_wg_routes()
    assert(#current <= 1, 'too many current routes')
    current = current[1]
    if current and util.has_value(active, current) then
        print('current route still active')
        return
    end
    if #active == 0 then
        print('no active tunnels')
        return
    end
    for _, act in pairs(active) do
        print('activating route for '..act)
        local id = tonumber(act:match('[0-9]+'))
        if set_wg_route(act, id) == 0 then
            break
        end
    end
end

function main()
    while true do
        update()
        sleep(10)
    end
end

main()


