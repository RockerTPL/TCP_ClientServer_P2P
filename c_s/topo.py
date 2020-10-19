from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections, quietRun
from mininet.log import setLogLevel, info
from mininet.cli import CLI
import time

class SingleSwitchTopo(Topo):
    def build(self, num_host=6, bw=10, delay='5ms', loss=0):
        # add switch
        s1 = self.addSwitch('s1')

        # add hosts
        hosts = [self.addHost('h{}'.format(i), ip='10.0.0.{}'.format(i+1)) for i in range(num_host)]

        # add links
        for i in range(num_host):
            self.addLink(hosts[i], s1, bw=bw, delay=delay, loss=loss, use_htb=True)

def Test():
    num_host = 6               # number of hosts
    num_peer = num_host - 1    # number of peers
    topo = SingleSwitchTopo(num_host)
    net = Mininet(topo=topo,
                  host=CPULimitedHost, link=TCLink,
                  autoStaticArp=False)
    net.start()
    info('* Dumping host connections\n')
    dumpNodeConnections(net.hosts)
    hosts = [net.getNodeByName('h{}'.format(i)) for i in range(num_host)]
    hosts[0].cmd('python server.py ./src/test > ./log/server &')
    for i in range(num_peer):
        hosts[i+1].cmd('python client.py ./dst/data%d/test > ./log/h%d &'
                       % (i+1, i+1))
    # CLI(net)
    time.sleep(120)
    net.stop()


if __name__ == '__main__':
    quietRun('sudo mn -c')
    setLogLevel('info')
    Test()
