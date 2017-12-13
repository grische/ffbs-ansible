#!/bin/sh

# run this as the vagrant user

cd /home/vagrant
if [ ! -d venv ]; then
  python3.6 -m venv venv
fi

. venv/bin/activate

cd /vagrant/python-dev/
pip install -e .
