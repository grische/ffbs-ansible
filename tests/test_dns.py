import pytest

testinfra_hosts = ['exit1', 'concentrator1', 'node1']

def test_resolve_google(host):
    host.check_output("sudo ip vrf exec freifunk host freifunk-bs.de 172.16.1.101")
