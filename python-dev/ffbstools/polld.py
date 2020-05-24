#!/usr/bin/env python3
import asyncio
import json
import random
import time
import traceback
import zlib

from aioetcd3.help import range_prefix
from influxdb import InfluxDBClient

from ffbstools.etcd import etcd_client

POLL_INTERVAL = 15
PRUNE_INTERVAL = 5*POLL_INTERVAL
CONFIG_PREFIX = '/config/'
YANIC_ADDR = ('::1', 11001)
REQUEST = 'GET nodeinfo statistics neighbours wireguard'.encode('ascii')

# dict of mesh mac addresses of indirect nodes, with {ip: insertion time} as value
meshed_mac_ips = dict()
# dict of mesh mac addresses of direct nodes, with insertion time as value
direct_macs = dict()
# map of last request timestamps
pings = dict()

def influxdb_wireguard(address, info):
    node_id = None
    for v in info.values():
        if 'node_id' in v:
            node_id = v['node_id']
    if node_id is None:
        print('no node_id found in data from', address[0])
        return
    if 'wireguard' not in info:
        print('no wireguard report found in data from', address[0])
        return
    points = []
    for if_name, if_info in info['wireguard']['interfaces'].items():
        for peer_key, peer_info in if_info['peers'].items():
            points.append({
                "measurement": "wireguard",
                "tags": {
                    "nodeid": node_id,
                    "interface": if_name,
                    "peer": peer_key,
                },
                "fields": {
                    "handshake": peer_info['latest_handshake'],
                    "rx": peer_info['transfer_rx'],
                    "tx": peer_info['transfer_tx'],
                },
            })
    influx.write_points(points)

def influxdb_delay(address, info, delay):
    node_id = None
    for v in info.values():
        if 'node_id' in v:
            node_id = v['node_id']
    if node_id is None:
        print('no node_id found in data from', address[0])
        return
    points = []
    points.append({
        "measurement": "respondd-delay",
        "tags": {
            "nodeid": node_id,
        },
        "fields": {
            "rtt": delay,
        },
    })
    influx.write_points(points)

class ResponddProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, address):
        delay = time.monotonic() - pings.get(address[0], 0.0)
        if delay > POLL_INTERVAL/10:
            delay = None

        self.transport.sendto(data, YANIC_ADDR)

        info = json.loads(inflate(data))
        #trace.write(json.dumps(info, indent=4)+'\n')

        influxdb_wireguard(address, info)

        if delay is not None:
            influxdb_delay(address, info, delay)

        print('received', address[0])
        if address[0].endswith('::1'):
            if info['nodeinfo']:
                for mesh in info['nodeinfo']['network']['mesh'].values():
                    for macs in mesh['interfaces'].values():
                        add_direct_macs(macs)
            if info['neighbours']:
                for neighs in info['neighbours']['batadv'].values():
                    for node in neighs['neighbours'].keys():
                        add_meshed_ip(node, mac_to_ipv6(node, address[0]))
        else:  # indirect response
            if info['nodeinfo']:
                for mesh in info['nodeinfo']['network']['mesh'].values():
                    for macs in mesh['interfaces'].values():
                        for mac in macs:
                            ack_meshed_ip(mac, address[0])

async def get_direct_ips():
    direct_ips = []
    raw = await etcd_client.range(key_range=range_prefix(CONFIG_PREFIX))
    for (k, v, meta) in raw:
        if k.decode('ascii').endswith('/address6'):
            direct_ips.append(v.decode('ascii'))
    return direct_ips

def get_meshed_ips():
    meshed_ips = set()
    for ips in meshed_mac_ips.values():
        print('ips', ips)
        best = max(ips.values())
        selected = random.choice([ip for ip, tries in ips.items() if tries == best])
        ips[selected] -= 1
        meshed_ips.add(selected)
    print('get_meshed_ips:\n from {}\n to {}'.format(meshed_mac_ips, meshed_ips))
    return list(meshed_ips)

async def task_poll_step(transport):
    loop = asyncio.get_event_loop()
    start = loop.time()
    nodes = await get_direct_ips()
    nodes += get_meshed_ips()
    print('nodes:', nodes)
    offset = POLL_INTERVAL / len(nodes)
    for i, node in enumerate(sorted(nodes)):
        print('polling', node)
        await asyncio.sleep(start + i*offset - loop.time())
        pings[node] = time.monotonic()
        transport.sendto(REQUEST, (node, 1001))

async def task_poll(transport):
    loop = asyncio.get_event_loop()
    offset = loop.time()
    while not loop.is_closed():
        try:
            await task_poll_step(transport)
        except asyncio.CancelledError:
            break
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()
        offset += POLL_INTERVAL
        await asyncio.sleep(offset - loop.time())

async def task_prune():
    while True:
        await asyncio.sleep(PRUNE_INTERVAL)
        print('pruning')
        old = time.monotonic() - PRUNE_INTERVAL
        print(direct_macs)
        for mac in [mac for mac, t in direct_macs.items() if t < old]:
            del direct_macs[mac]
        for ips in meshed_mac_ips.values():
            for ip in [ip for ip, tries in ips.items() if tries <= 0]:
                del ips[ip]
        for mac in [mac for mac, ips in meshed_mac_ips.items() if not ips]:
            del meshed_mac_ips[mac]

def add_direct_macs(macs):
    now = time.monotonic()
    for mac in macs:
        direct_macs[mac] = now
        meshed_mac_ips.pop(mac, None)

def add_meshed_ip(mac, ip):
    if mac in direct_macs:
        return
    ips = meshed_mac_ips.setdefault(mac, {})
    ips[ip] = max(ips.get(ip, 0), 5)

def ack_meshed_ip(mac, ip):
    if mac in direct_macs:
        return
    ips = meshed_mac_ips.get(mac, {})
    if ip not in ips:
        return
    ips[ip] = max(ips.get(ip, 0), 10)

def inflate(data):
    decompress = zlib.decompressobj(-zlib.MAX_WBITS)
    inflated = decompress.decompress(data)
    inflated += decompress.flush()
    return inflated.decode()

def mac_to_ipv6(mac, prefix):
    parts = mac.split(':')
    parts.insert(3, 'ff')
    parts.insert(4, 'fe')
    parts[0] = "%x" % (int(parts[0], 16) ^ 2)
    ipv6 = [prefix.split('::', 1)[0]]
    for i in range(0, len(parts), 2):
        ipv6.append(''.join(parts[i:i+2]))
    return ':'.join(ipv6)

#trace = open('/tmp/polld-trace', 'w')
influx = InfluxDBClient(database='ffbs')

def main():
    loop = asyncio.get_event_loop()
    listen = loop.create_datagram_endpoint(ResponddProtocol, local_addr=('::', 0))
    transport, protocol = loop.run_until_complete(listen)
    loop.create_task(task_poll(transport))
    loop.create_task(task_prune())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    transport.close()
    loop.close()

if __name__ == '__main__':
    main()
