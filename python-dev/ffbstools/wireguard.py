#!/usr/bin/env python3

import json, subprocess

def get_dict():
    output = subprocess.check_output("wg show all dump".split()).decode('ascii')
    result = {}
    peers = None
    for line in output.splitlines():
        line = line.strip().split()
        if not line:
            continue
        device = result.setdefault(line[0], {})
        if not device:
            device['private_key'] = line[1]
            device['public_key'] = line[2]
            device['listen_port'] = int(line[3])
            peers = device['peers'] = {}
        else:
            peer = peers[line[1]] = {}
            if line[2] != "(none)":
                peer['preshared_key'] = line[2]
            peer['endpoint'] = line[3]
            peer['allowed-ips'] = line[4].split(',')
            peer['latest_handshake'] = int(line[5])
            peer['transfer_rx'] = int(line[6])
            peer['transfer_tx'] = int(line[7])
            peer['presistent_keepalive'] = int(line[8])
    return result

def get_json():
    return json.dumps(get_dict(), indent=2, sort_keys=True)

if __name__ == "__main__":
    print(get_json())
