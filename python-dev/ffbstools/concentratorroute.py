#!/usr/bin/env python3

import subprocess, time
from pprint import pprint

from pyroute2 import IPRoute
from pyroute2.netlink.rtnl import rt_type

from . import wireguard

WG_TIMEOUT = 180
TABLE = 10
RT_PROTO = 23

def get_wg_active_nets():
    result = []
    now = time.time()
    wg = wireguard.get_dict()
    for iface, data in wg.items():
        for peer in data['peers'].values():
            if (now - peer['latest_handshake']) > WG_TIMEOUT:
                continue
            for ip in peer['allowed_ips']:
                # we're not interested in default routes
                if not ip.endswith('/0'):
                    result.append(ip)
    result.sort()
    return result

def get_wg_links():
    result = {}
    ip = IPRoute()
    for link in ip.get_links():
        linkinfo = link.get_attr('IFLA_LINKINFO')
        if not linkinfo:
            continue
        info_kind = linkinfo.get_attr('IFLA_INFO_KIND')
        if not info_kind == 'wireguard':
            continue
        operstate = link.get_attr('IFLA_OPERSTATE')
        if operstate == 'DOWN':
            continue
        ifname = link.get_attr('IFLA_IFNAME')
        result[link['index']] = ifname
        result[ifname] = link['index']
    return result

def get_wg_routes():
    result = []
    ip = IPRoute()
    for route in ip.get_routes(table=TABLE):
        if not route['type'] == rt_type['unicast']:
            continue
        if not route['proto'] == RT_PROTO:
            continue
        oif = route.get_attr('RTA_OIF')
        result.append('{}/{}'.format(route.get_attr('RTA_DST'), route['dst_len']))
    return result

def set_wg_route(oif, dst, action):
    dst, dst_len = dst.split('/', 1)
    dst_len = int(dst_len)
    ip = IPRoute()
    ip.route(action,
        table=TABLE,
        proto=RT_PROTO,
        oif=oif,
        type='unicast',
        dst='{}/{}'.format(dst, dst_len),
    )


def update():
    active = set(get_wg_active_nets())
    links = get_wg_links()
    link_id = links['wg-nodes']
    current = set(get_wg_routes())

    #pprint(link_id)
    #pprint(active)
    #pprint(current)

    new = active - current
    old = current - active

    for dst in new:
        print("adding route for {}".format(dst))
        set_wg_route(link_id, dst, 'add')

    for dst in old:
        print("deleting route for {}".format(dst))
        set_wg_route(link_id, dst, 'delete')

def main():
    while True:
        update()
        time.sleep(10)

if __name__  == "__main__":
    main()
