import asyncio

from aioetcd3.client import client
from aioetcd3.help import range_all
from aioetcd3.kv import KV
from aioetcd3 import transaction

etcd_client = client(endpoint="127.0.0.1:2379")

import json

async def put():
    await etcd_client.put('/foo', 'foo')
    
    value, meta = await etcd_client.get('/foo')
    
    value_list = await etcd_client.range(range_all())
    
    await etcd_client.put('/foo/bar', json.dumps({'a': 2, 'b': True, 'c': [1,2,3]}))

    #await etcd_client.delete('/foo')
    
    #lease =await etcd_client.grant_lease(ttl=5)
    
    #await etcd_client.put('/foo1', 'foo', lease=lease)
    
def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(put())

if __name__ == "__main__":
    main()
