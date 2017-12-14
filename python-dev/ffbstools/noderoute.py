#!/usr/bin/env python3

import subprocess, time
from pprint import pprint

from pyroute2 import IPRoute
from pyroute2.netlink.rtnl import rt_type

from . import wireguard

TABLE = 10
RT_PROTO = 23

IDS = {
    'wg-c1': 1,
    'wg-c2': 2,
    'wg-c3': 3,
}


def get_handshake_ages():
    result = []
    now = time.time()
    wg = wireguard.get_dict()
    for iface, data in wg.items():
        peers = data['peers']
        if not len(peers)==1:
            continue
        _, peer = peers.popitem()
        result.append((now - peer['latest_handshake'], iface))
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
        pprint(link)
        ifname = link.get_attr('IFLA_IFNAME')
        result[link['index']] = ifname
        result[ifname] = link['index']
    return result

def get_wg_routes():
    result = []
    ip = IPRoute()
    for route in ip.get_routes(table=TABLE):
        if not route.get_attr('RTA_DST') is None:
            continue
        if not route['dst_len'] == 0:
            continue
        if not route['type'] == rt_type['unicast']:
            continue
        if not route['proto'] == RT_PROTO:
            continue
        oif = route.get_attr('RTA_OIF')
        result.append(oif)
    return result

def set_wg_route(oif, id):
    ip = IPRoute()
    ip.route('replace',
        table=TABLE,
        proto=RT_PROTO,
        oif=oif,
        type='unicast',
        dst_len=0,
        gateway='10.0.0.{}'.format(id),
    )


def update():
    active = [iface for age, iface in get_handshake_ages() if age < 180]
    #current = get_current():
    links = get_wg_links()
    current = [links[index] for index in get_wg_routes()]
    assert len(current) <= 1
    current = current[0] if current else None

    #pprint(active)
    #pprint(current)
    if current and current in active:
        print("current route still active")
        return

    if not active:
        print("no active tunnels")
        return

    print("activating route for {}".format(active[0]))
    set_wg_route(links[active[0]], IDS[active[0]])

def main():
    update()
    time.sleep(10)

if __name__  == "__main__":
    main()
