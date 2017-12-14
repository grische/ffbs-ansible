testinfra_hosts = ['concentrator1', 'concentrator2', 'concentrator3']

def test_installed(host):
    assert host.package("etcd-server").is_installed
    assert host.package("etcd-client").is_installed
    assert host.service("etcd").is_enabled

def test_health(host):
    assert host.service("etcd").is_running

