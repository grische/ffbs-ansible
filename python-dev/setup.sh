#!/bin/sh

# run this as the vagrant user

cd /home/vagrant
if [ ! -d venv ]; then
  python3.6 -m venv venv
fi

. venv/bin/activate

pip install aioetcd3 aiohttp pyroute2
