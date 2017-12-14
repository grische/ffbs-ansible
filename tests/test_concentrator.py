testinfra_hosts = ['concentrator1', 'concentrator2', 'concentrator3']

def test_routing_enabled(host):
    assert host.sysctl("net.ipv4.ip_forward")
    assert host.sysctl("net.ipv6.conf.all.forwarding=1")
