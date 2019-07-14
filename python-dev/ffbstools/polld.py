#!/usr/bin/env python3
import asyncio
import json
import time
import zlib

from aioetcd3.help import range_prefix

from ffbstools.etcd import etcd_client

POLL_INTERVAL = 10
PRUNE_INTERVAL = 15
CONFIG_PREFIX = '/config/'
YANIC_ADDR = ('::1', 11001)
REQUEST = 'GET nodeinfo statistics neighbours wireguard'.encode('ascii')

# list of meshed nodes, map from mesh mac address to (ipv6, insertion time)
indirect = dict()
# list of mesh mac addresses of direct nodes to ignore, map from mac addres to insertion time
blacklist = dict()

class ResponddProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, address):
        self.transport.sendto(data, YANIC_ADDR) 
        if address[0].endswith('::1'):
            info = json.loads(inflate(data))
            if info['nodeinfo']:
                for mesh in info['nodeinfo']['network']['mesh'].values():
                    for macs in mesh['interfaces'].values():
                        add_to_blacklist(macs)
            if info['neighbours']:
                print('got neighbours of', address[0])
                for neighs in info['neighbours']['batadv'].values():
                    for node in neighs['neighbours'].keys():
                        if node not in blacklist:
                            indirect[node] = mac_to_ipv6(node, address[0]), time.monotonic()


async def get_direct_nodes():
    raw = await etcd_client.range(key_range=range_prefix(CONFIG_PREFIX))
    direct = []
    for (k, v, meta) in raw:
        if k.decode('ascii').endswith('/address6'):
            direct.append(v.decode('ascii'))
    return direct

async def task_poll(transport):
    loop = asyncio.get_event_loop()
    start = loop.time()
    while True:
        nodes = await get_direct_nodes()
        nodes += [addr for addr, _ in indirect.values()]
        print('nodes:', nodes)
        offset = POLL_INTERVAL / len(nodes)
        for i, node in enumerate(nodes):
            print('polling', node)
            await asyncio.sleep(start + i*offset - loop.time())
            transport.sendto(REQUEST, (node, 1001))
        start += POLL_INTERVAL

async def task_prune():
    global indirect, blacklist
    while True:
        await asyncio.sleep(PRUNE_INTERVAL)
        print('pruning')
        old = time.monotonic() - 5 * POLL_INTERVAL
        indirect = {mac:v for mac, v in indirect.items() if v[1] < old}
        blacklist = {mac:t for mac, t in blacklist.items() if t < old}

def add_to_blacklist(macs):
    now = time.monotonic()
    blacklist.update(map(lambda x: (x, now), macs))
    [indirect.pop(mac) for mac in macs if mac in indirect]

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
