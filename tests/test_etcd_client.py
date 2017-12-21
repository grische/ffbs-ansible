testinfra_hosts = ['concentrator1', 'concentrator2', 'concentrator3', 'exit1']

def test_client_status(host):
    output = host.check_output(". /etc/profile.d/etcd.sh && etcdctl endpoint status").splitlines()
    assert len(output) == 3

def test_client_health(host):
    output = host.check_output(". /etc/profile.d/etcd.sh && etcdctl endpoint health").splitlines()
    assert len(output) == 3
