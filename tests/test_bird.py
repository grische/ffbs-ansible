import pytest
from io import StringIO
from textfsm import TextFSM

testinfra_hosts = ['concentrator1', 'concentrator2', 'concentrator3']

OSPF_NEIGHBORS = TextFSM(StringIO("""
Value RouterID (\d+(\.\d+){3})
Value Pri (\d+)
Value DTime (\S+)
Value State (\S+)
Value Interface (\S+)
Value RouterIP (\d+(\.\d+){3})

Start
  # Router ID     Pri   State    DTime   Interface  Router IP 
  # 172.16.1.2    1     Full/PtP 00:31   wg-c2      172.16.1.2
  ^${RouterID}\s+${Pri}\s+${State}\s+${DTime}\s+${Interface}\s+${RouterIP} -> Record

EOF
""".strip()))
def test_ospf_neighbors(host):
    OSPF_NEIGHBORS.Reset()
    data = OSPF_NEIGHBORS.ParseText(host.check_output("sudo birdc show ospf neighbors"))
    assert len(data) == len(testinfra_hosts) - 1
