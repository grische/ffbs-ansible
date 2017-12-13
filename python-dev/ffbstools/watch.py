import asyncio

from aioetcd3.client import client
from aioetcd3.help import range_all, range_prefix
from aioetcd3 import transaction

etcd_client = client(endpoint="127.0.0.1:2379")

async def watch():
    async with etcd_client.watch_scope(range_prefix('/foo')) as response:
        async for event in response:
            print(event)
    
async def main():
    await watch()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
