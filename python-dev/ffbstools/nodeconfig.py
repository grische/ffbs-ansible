#!/usr/bin/env python3
import json
import random
import os
import requests
import string
import subprocess
import time

import ipaddress

def addresses_from_number(num):
    """calculates the client's addresses from its 14bit number"""
    v6base = 0x20010bf70381 << 80
    range_size = 10
    def as_v4(n):
        return str(ipaddress.IPv4Address(n))
    def as_v6(n):
        return str(ipaddress.IPv6Address(n))
    address4 = as_v4(0xac110000 | num)
    range4 = as_v4(0x0a000000 | (num << range_size))+'/'+str(32-range_size)
    address6 = as_v6(v6base | (num << 64) + 1)
    range6 = as_v6(v6base | (num << 64))+'/64'
    return dict(address4=address4, range4=range4, address6=address6, range6=range6)

HOST = 'concentrator1:8080'
TEMPDIR = '/tmp/ff-ka7Ohp1i/'

def get_wg_info():
    output = subprocess.check_output(['wg','show','all','dump']).decode()
    pubkey = output.split('\n',1)[0].split('\t')[2]
    ifaces = set([l.split('\t',1)[0] for l in output.split('\n') if l])
    return pubkey, ifaces

def fetch_config(pubkey):
    nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    files = ['config', 'config.sig']
    text = dict()
    for fname in files:
        r = requests.get('http://{}/{}?pubkey={}&nonce={}'.format(HOST, fname, pubkey, nonce))
        if r.status_code == 200:
            with open(TEMPDIR+fname, 'w') as f:
                f.write(r.text)
                text[fname] = r.text
        else:
            return None
    rtn = subprocess.call(['signify-openbsd','-V','-p','/etc/ffbs/node-config-pub.key','-m',TEMPDIR+'config'])
    if rtn != 0:
        return None
    conf = json.loads(text['config'])
    if nonce != conf['nonce']:
        return None
    del conf['nonce']
    return conf

def apply_config(conf, ifaces):
    pass

if __name__ == '__main__':
    print(addresses_from_number(0))
    if not os.path.exists(TEMPDIR):
        os.makedirs(TEMPDIR)
    pubkey, ifaces = get_wg_info()
    # ifaces is obsolete, since we need to create the wg intefaces depending on the config
    while True:
        conf = fetch_config(pubkey)
        if conf:
            apply_config(conf, ifaces)
            time.sleep(conf['retry'])
        else:
            time.sleep(10)

