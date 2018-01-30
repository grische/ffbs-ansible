#!/bin/bash
source /etc/profile.d/etcd.sh
PUT="etcdctl put"
GET="etcdctl get"

etcdctl endpoint health
if [[ $? -gt 0 ]]; then
    echo "cluster unhealthy, skipping"
    exit 0
fi

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
$PUT '/config/default/concentrators' '[{"address4": "10.0.0.1", "address6": "2001:bf7:381::1", "endpoint": "concentrator1:2300", "pubkey": "LfwcsPGyih7XpzUHCEaCpoJWP0JzYOFv9ElfItlgAiM=", "id": 1}, {"address4": "10.0.0.2", "address6": "2001:bf7:381::2", "endpoint": "concentrator2:2300", "pubkey": "whT6vlbUGSBKzKJGlxhevJf/PU/Jvdi9P6oSzAZ0i0E=", "id": 2}, {"address4": "10.0.0.3", "address6": "2001:bf7:381::3", "endpoint": "concentrator3:2300", "pubkey": "Xzzv10CknsICmteoJCGwHkERtVhS6xkT6LzPCrDxURM=", "id": 3}]'

$PUT 'next_free_id' 1
$PUT 'initialized' "$(date)"

