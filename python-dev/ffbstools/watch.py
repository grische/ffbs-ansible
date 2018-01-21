import asyncio

from aioetcd3.help import range_all, range_prefix
from aioetcd3 import transaction

from .etcd import etcd_client


async def watch():
    async with etcd_client.watch_scope(range_prefix('/foo')) as response:
        async for event in response:
            print(event)
    
def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(watch())

if __name__ == "__main__":
    main()
