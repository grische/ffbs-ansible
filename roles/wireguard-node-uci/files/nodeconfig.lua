local json = require('luci.jsonc')
local uci = require('uci')
local util = require('util')

local config_file = arg[1]
local nonce = arg[2]

local DHCP_IFACE="br-br0"
local PRIVKEY="/etc/ffbs/wg-privkey"

local function dump(obj)
    print(json.stringify(obj))
end

function conf_wg_iface(iface, privkey, peers, keepalive)
    local cmd = 'wg set '..iface
    if privkey ~= nil then
        cmd = cmd..' private-key '..privkey
    end
    for _,peer in pairs(peers) do
        cmd = cmd..' peer '..peer.pubkey..' endpoint '..peer.endpoint
        cmd = cmd..' persistent-keepalive '..keepalive..' allowed-ips 0.0.0.0/0'
    end
    os.execute(cmd)
end

function apply_wg(conf)
    --TODO Apply MTU
    local current = util.get_wg_info()
    local target_ifaces = {}
    for _, conc in pairs(conf.concentrators) do
        local iface = 'wg_c'..conc.id
        target_ifaces[iface] = conc
        if current[iface] == nil then
            os.execute('ip link add '..iface..' type wireguard')
            conf_wg_iface(iface, PRIVKEY, {conc}, conf.wg_keepalive)
            os.execute('ip link set up '..iface)
        end
    end
    for iface, wg_conf in pairs(current) do
        if target_ifaces[iface] == nil then
            os.execute('ip link del '..iface)
        else
            if util.tablelength(wg_conf.peers) <= 1 then
                local target = target_ifaces[iface]
                local cur_conf = {}
                for pubkey, peer in pairs(wg_conf.peers) do
                    cur_conf.pubkey = pubkey
                    cur_conf.endpoint = peer.endpoint
                end
                local endp = util.str_split(target.endpoint, '[^:]+')
                endp[1] = util.nslookup(endp[1])
                target.endpoint = endp[1]..':'..endp[2]
                local diff = {}
                if util.tablelength(cur_conf) > 0 then
                    for k,v in pairs(cur_conf) do
                        if target[k] ~= v then
                            diff[k] = target[k]
                        end
                    end
                else
                    diff = target
                end
                if util.tablelength(diff) > 0 then
                    if diff.pubkey ~= nil and cur_conf.pubkey ~= nil then
                        os.execute('wg set '..iface..' peer '..cur_conf.pubkey..' remove')
                    end
                    conf_wg_iface(iface, PRIVKEY, {target}, conf.wg_keepalive)
                end
            end
        end
    end
    -- check ip addresses
    for iface, conc in pairs(target_ifaces) do
        -- TODO make this more beautiful
        dump(os.execute('ip addr flush dev '..iface..' scope global'))
        dump(os.execute('ip addr add '..conf.address4..'/32 peer '..conc.address4..' dev '..iface))
        dump(os.execute('ip addr replace '..conf.address6..'/128 peer '..conc.address6..' dev '..iface))
    end
    return true
end

function apply_dhcp(conf)
    local x = uci.cursor()
    local prefix_len = tonumber(util.str_split(conf.range4, '[^/]+')[2])
    local limit = (2^(32-prefix_len)-2)

    if x:get('dhcp', DHCP_IFACE) == nil then
        x:set('dhcp', DHCP_IFACE, 'dhcp')
    end
    x:set('dhcp', DHCP_IFACE, 'interface', DHCP_IFACE)
    x:set('dhcp', DHCP_IFACE, 'leasetime', '15m')
    x:set('dhcp', DHCP_IFACE, 'start', '2')
    x:set('dhcp', DHCP_IFACE, 'limit', limit)

    local changes = x:changes()
    dump(changes)
    for _,_ in pairs(changes) do -- hacky version of if not empty table
        return x:commit('dhcp')
    end
    return true
end

conf = json.parse(util.read_file(config_file))
-- dump(conf)

if conf.nonce ~= nonce then
    print('nonce does not match')
    os.exit(1)
end

if conf.id ~= nil then
    -- we got data, let's do stuff
    res_wg = apply_wg(conf)
    res_dhcp = apply_dhcp(conf)
    if not (res_dhcp and res_wg) then
        os.exit(1)
    end
end

print(conf.retry)

