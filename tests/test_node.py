import pytest

testinfra_hosts = ['node1']

@pytest.mark.parametrize('concentrator', ['10.0.0.1', '10.0.0.2', '10.0.0.3'])
def test_ping_concentrator(host, concentrator):
    host.check_output("ping -c 1 -I freifunk {}".format(concentrator))
     
def test_ping_google(host):
    host.check_output("ping -c 1 -I freifunk 8.8.8.8")
