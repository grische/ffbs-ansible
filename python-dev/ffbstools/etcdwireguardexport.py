#!/srv/venv/bin/python3
import asyncio
import traceback
from socket import gethostname
import json

from aioetcd3.client import client

from .wireguard import get_dict

etcd_client = client(endpoint="127.0.0.1:2379")


async def update(lease):
    for interface, data in get_dict().items():
        key = "/wireguard/{}/{}".format(gethostname(), interface)

        await etcd_client.put(
            key,
            json.dumps(data, indent=2, sort_keys=True),
            lease=lease
        )

async def main_loop():
    lease = await etcd_client.grant_lease(ttl=15)
    while True:
        try:
            await update(lease)
        except:
            traceback.print_exc()
        lease = await lease.refresh()
        if not lease.ttl:
            print("lease timeout")
            exit(1)
        await asyncio.sleep(10)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_loop())

if __name__ == "__main__":
    main()
