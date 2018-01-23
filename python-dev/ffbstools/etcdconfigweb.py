#!/usr/bin/env python3
import asyncio
import json
import re
import time

from subprocess import check_output

from aioetcd3.help import range_prefix
from aioetcd3.kv import KV
from aioetcd3 import transaction

from aiohttp import web

from .etcd import etcd_client
from .util import addresses_from_number


EXPIRE_TIME=60
RETRY_TIME_FOR_REGISTERED=600

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

async def insert_new_node(pubkey):
    success = False
    while not success:
        next_id_raw, _ = await etcd_client.get('next_free_id')
        next_id = int(next_id_raw)
        info = addresses_from_number(next_id)
        info['retry'] = RETRY_TIME_FOR_REGISTERED
        info['id'] = next_id
        on_success = [KV.put.txn('/config/{}/{}'.format(pubkey,k), str(v)) for k,v in info.items()]
        on_success = [KV.put.txn('next_free_id', str(next_id+1))] + on_success
        compare = [transaction.Value('next_free_id') == next_id_raw]
        success, _ = await etcd_client.txn(compare=compare, success=on_success)

async def config_for(pubkey, no_retry=False):
    config = dict()
    for key in ['default', pubkey]:
        raw = await etcd_client.range(key_range=range_prefix('/config/{}/'.format(key)))
        config.update(dict([(a[0].decode().split('/', 3)[-1], conv_val(a[1])) for a in raw]))
    if not 'id' in config and not no_retry:
        await insert_new_node(pubkey)
        config = await config_for(pubkey, no_retry=True)
    return config

async def web_config(request):
    if 'pubkey' in request.query and 'nonce' in request.query:
        pubkey = request.query.get('pubkey')
        nonce = request.query.get('nonce')
        if pubkey and nonce:
            raw = await config_for(pubkey)
            raw['nonce'] = nonce
            conf = json.dumps(raw)
            sig = await get_signature(conf)
            sig_cache[(pubkey,nonce)] = (sig, time.time())
            return web.Response(content_type='application/json', text=conf)
        else:
            return web.Response(status=400)
    else:
        return web.Response(status=400)

async def web_config_sig(request):
    if 'pubkey' in request.query and 'nonce' in request.query:
        pubkey = request.query.get('pubkey')
        nonce = request.query.get('nonce')
        if pubkey:
            if (pubkey,nonce) in sig_cache:
                sig = sig_cache[(pubkey,nonce)][0]
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

