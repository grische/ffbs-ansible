#!/srv/venv/bin/python3
import asyncio
import json
import re

from aioetcd3.client import client
from aioetcd3.help import range_prefix

from aiohttp import web

etcd_client = client(endpoint="127.0.0.1:2379")

def conv_val(raw):
    try:
        return json.loads(raw.decode())
    except json.decoder.JSONDecodeError:
        return raw.decode()

async def config_for(client):
    config = dict()
    for key in ['default', client]:
        raw = await etcd_client.range(key_range=range_prefix('/config/{}/'.format(key)))
        config.update(dict([(a[0].decode().split('/', 3)[-1], conv_val(a[1])) for a in raw]))
    return config

async def web_config(request):
    if 'pubkey' in request.query:
        client = request.query.get('pubkey')
        if client:
            conf = json.dumps(await config_for(client))
            return web.Response(content_type='application/json', text=conf)
        else:
            return web.Response(status=400)
    else:
        return web.Response(status=400)

def main():
    app = web.Application()
    app.router.add_get('/config', web_config)
    web.run_app(app, host=('::','0.0.0.0'), port=8080)

if __name__ == "__main__":
    main()

