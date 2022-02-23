#!/usr/bin/env python3
import asyncio
import base64
import binascii
import json
import socket
import time

from aioetcd3.help import range_prefix
from aioetcd3.kv import KV
from aioetcd3 import transaction

from aiohttp import web

try:
    from .etcd import etcd_client
    from . import util
except ModuleNotFoundError:
    # running directly from CLI?
    from etcd import etcd_client
    import util


RETRY_TIME_FOR_REGISTERED=600

requests_failed = 0
requests_successful = 0

class ResolveError(Exception):
    pass

def conv_val(raw):
    try:
        return json.loads(raw.decode())
    except json.decoder.JSONDecodeError:
        return raw.decode()

async def resolve(host, port, force_v4=False):
    loop = asyncio.get_event_loop()
    family = socket.AF_INET if force_v4 else socket.AF_INET6
    result = await loop.getaddrinfo(host, port, family=family, proto=socket.IPPROTO_UDP)
    if len(result) == 0:
        raise ResolveError()
    else:
        ip = result[0][4][0]
        return ip if force_v4 else '['+ip+']'

async def check_output_aio(cmd, inp=None):
    proc = await asyncio.create_subprocess_shell(cmd,
                             stdout=asyncio.subprocess.PIPE, stdin=asyncio.subprocess.PIPE)
    if inp is not None:
        proc.stdin.write(inp.encode())
        proc.stdin.write_eof()
    await proc.wait()
    data = await proc.stdout.read()
    outp = data.decode('ascii')
    return outp

async def get_signature(msg):
    sig = await check_output_aio("signify-openbsd -S -m'-' -s /etc/ffbs/node-config.sec -x-", msg)
    return sig.split('\n')[1]

async def insert_new_node(pubkey_esc):
    success = False
    while not success:
        next_id_raw, _ = await etcd_client.get('next_free_id')
        next_id = int(next_id_raw)
        info = util.addresses_from_number(next_id)
        info['retry'] = RETRY_TIME_FOR_REGISTERED
        info['id'] = next_id
        on_success = [KV.put.txn('/config/{}/{}'.format(pubkey_esc,k), str(v)) for k,v in info.items()]
        on_success = [KV.put.txn('next_free_id', str(next_id+1))] + on_success
        compare = [transaction.Value('next_free_id') == next_id_raw]
        success, _ = await etcd_client.txn(compare=compare, success=on_success)

async def config_for(pubkey_esc, no_retry=False):
    config = dict()
    for key in ['default', pubkey_esc]:
        raw = await etcd_client.range(key_range=range_prefix('/config/{}/'.format(key)))
        config.update(dict([(a[0].decode().split('/', 3)[-1], conv_val(a[1])) for a in raw]))
    if not 'id' in config and not no_retry:
        await insert_new_node(pubkey_esc)
        config = await config_for(pubkey_esc, no_retry=True)
    return config

async def web_config(request):
    global requests_failed, requests_successful
    try:
        v6mtu = request.query.get('v6mtu', None)
        if v6mtu is not None:
            v6mtu = int(v6mtu)
    except:
        print("failed to handle v6mtu: {}".format(v6mtu))
        v6mtu = None
    if 'pubkey' in request.query and 'nonce' in request.query and v6mtu:
        pubkey = request.query.get('pubkey').replace(' ','+')
        try:
            raw_pubkey = base64.standard_b64decode(pubkey)
            pubkey_esc = base64.urlsafe_b64encode(raw_pubkey)
            pubkey_valid = (len(raw_pubkey) == 32)
        except binascii.Error:
            pubkey_valid = False
        nonce = request.query.get('nonce')
        if pubkey_valid and pubkey_esc and nonce:
            raw = await config_for(pubkey_esc)
            force_v4 = ':' not in request.headers.get('x-real-ip', '')
            if v6mtu is not None and v6mtu < 1455:
                # 1375+40+8+4+4+8+16, see https://www.mail-archive.com/wireguard@lists.zx2c4.com/msg01856.html
                force_v4 = True
                print("v6mtu {} too small, using v4".format(v6mtu))
            for concentrator in raw.get('concentrators', []):
                if 'endpoint' not in concentrator:
                    continue
                host, port = concentrator['endpoint'].split(':', 1)
                resolved = await resolve(host, int(port), force_v4)
                concentrator['endpoint'] = ':'.join((resolved, port))
            raw['nonce'] = nonce
            raw['time'] = int(time.time())
            conf = json.dumps(raw)+'\n'
            sig = await get_signature(conf)
            requests_successful += 1
            return web.Response(content_type='text/plain', text=conf+sig)
        else:
            requests_failed += 1
            return web.Response(status=400)
    else:
        requests_failed += 1
        return web.Response(status=400)

async def web_etcd_status(request):
    raw = await etcd_client.range_keys(key_range=range_prefix('/config/'))
    node_count = len([1 for key, _ in raw if b'id' in key])
    status = dict(requestsFailed=requests_failed, requestsSuccessful=requests_successful, nodesConfigured=node_count)
    return web.Response(content_type='application/json', text=json.dumps(status))

def main():
    app = web.Application()
    app.router.add_get('/config', web_config)
    app.router.add_get('/etcd_status', web_etcd_status)
    loop = asyncio.get_event_loop()
    handler = app.make_handler()
    f = loop.create_server(handler, ('::','0.0.0.0'), 8080)
    srv = loop.run_until_complete(f)
    print('serving on', [s.getsockname() for s in srv.sockets])
    loop.run_forever()

if __name__ == "__main__":
    main()
