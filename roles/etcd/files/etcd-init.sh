#!/bin/bash
source /etc/profile.d/etcd.sh
PUT="etcdctl put"
GET="etcdctl get"

# do not overwrite these values
initialized=$($GET initialized)
if [[ -n "$initialized" ]]; then
    echo "already initialized, aborting"
    exit 0
fi

# insert default values
$PUT '/config/default/retry' 20
$PUT '/config/default/wg_keepalive' 25
$PUT '/config/default/mtu' 1420
$PUT '/config/default/concentrators' '[{"address4": "10.0.0.1", "address6": "2001:bf7:381::1", "endpoint": "concentrator1:2300", "pubkey": "LfwcsPGyih7XpzUHCEaCpoJWP0JzYOFv9ElfItlgAiM=", "id": 1}, {"address4": "10.0.0.2", "address6": "2001:bf7:381::2", "endpoint": "concentrator2:2300", "pubkey": "whT6vlbUGSBKzKJGlxhevJf/PU/Jvdi9P6oSzAZ0i0E=", "id": 2}, {"address4": "10.0.0.1", "address6": "2001:bf7:381::3", "endpoint": "concentrator3:2300", "pubkey": "Xzzv10CknsICmteoJCGwHkERtVhS6xkT6LzPCrDxURM=", "id": 3}]'

# insert test client (num 0x3fff)
$PUT '/config/test/retry' 600
$PUT '/config/test/id' 16383
$PUT '/config/test/address4' '10.255.252.1'
$PUT '/config/test/range4' '10.255.252.0/22'
$PUT '/config/test/address6' '2001:bf7:381:3fff::1'
$PUT '/config/test/range6' '2001:bf7:381:3fff::/64'


$PUT 'next_free_id' 1
$PUT 'initialized' "$(date)"

