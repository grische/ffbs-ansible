#!/usr/bin/env python3
import asyncio
import json
import re
import time

from subprocess import check_output

from aioetcd3.client import Client
from aioetcd3.help import range_prefix

from aiohttp import web

EXPIRE_TIME=60

ca = open('/etc/ssl/etcd/etcd-ca.pem', 'rb')
client = open('/etc/ssl/etcd/etcd-client.cert.pem', 'rb')
key = open('/etc/ssl/etcd/etcd-client.key.pem', 'rb')

own_ip = re.search('inet ([0-9.]+) peer [^\n]+ wg-c',check_output(['ip','a']).decode()).group(1)
etcd_client = Client(endpoint="{}:2379".format(own_ip), ssl=True, cert_cert=client.read(), ca_cert=ca.read(), cert_key=key.read())

sig_cache = dict()

def conv_val(raw):
    try:
        return json.loads(raw.decode())
    except json.decoder.JSONDecodeError:
        return raw.decode()

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
    return await check_output_aio("signify-openbsd -S -m'-' -s /etc/ffbs/node-config-priv.key -x-", msg)

async def config_for(client):
    config = dict()
    for key in ['default', client]:
        raw = await etcd_client.range(key_range=range_prefix('/config/{}/'.format(key)))
        config.update(dict([(a[0].decode().split('/', 3)[-1], conv_val(a[1])) for a in raw]))
    return config

async def web_config(request):
    if 'pubkey' in request.query and 'nonce' in request.query:
        client = request.query.get('pubkey')
        nonce = request.query.get('nonce')
        if client:
            raw = await config_for(client)
            raw['nonce'] = nonce
            conf = json.dumps(raw)
            sig = await get_signature(conf)
            sig_cache[(client,nonce)] = (sig, time.time())
            return web.Response(content_type='application/json', text=conf)
        else:
            return web.Response(status=400)
    else:
        return web.Response(status=400)

async def web_config_sig(request):
    if 'pubkey' in request.query and 'nonce' in request.query:
        client = request.query.get('pubkey')
        nonce = request.query.get('nonce')
        if client:
            if (client,nonce) in sig_cache:
                sig = sig_cache[(client,nonce)][0]
                return web.Response(content_type='text/plain', text=sig)
            else:
                return web.Response(status=404)
        else:
            return web.Response(status=400)
    else:
        return web.Response(status=400)

async def cleanup():
    while True:
        now = time.time()
        for k in list(sig_cache.keys()):
            if now-EXPIRE_TIME > sig_cache[k][1]:
                del sig_cache[k]
        await asyncio.sleep(EXPIRE_TIME)

def main():
    print('connecting to {}'.format(own_ip))
    app = web.Application()
    app.router.add_get('/config', web_config)
    app.router.add_get('/config.sig', web_config_sig)
    loop = asyncio.get_event_loop()
    handler = app.make_handler()
    f = loop.create_server(handler, ('::','0.0.0.0'), 8080)
    srv = loop.run_until_complete(f)
    cleaner = loop.create_task(cleanup())
    print('serving on', [s.getsockname() for s in srv.sockets])
    loop.run_forever()

if __name__ == "__main__":
    main()

