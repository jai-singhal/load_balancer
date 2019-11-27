from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import CPULimitedHost, Host, Node

class MyTopo( Topo ):

    def build( self ):
        "Create custom topo."

        info( '*** Add switches\n')
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch)
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch)

        info( '*** Add hosts\n')
        h1 = self.addHost('h1', cls=Host, defaultRoute=None)
        h2 = self.addHost('h2', cls=Host, defaultRoute=None)
        h3 = self.addHost('h3', cls=Host, defaultRoute=None)
        h4 = self.addHost('h4', cls=Host, defaultRoute=None)
        h5 = self.addHost('h5', cls=Host, defaultRoute=None)
        h6 = self.addHost('h6', cls=Host, defaultRoute=None)

        info( '*** Add links\n')
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        self.addLink(s1,s2,bw=5)
        self.addLink(s1,s2,bw=5)
        self.addLink(s1,s2,bw=5)
        self.addLink(h4, s2)
        self.addLink(h5, s2)
        self.addLink(h6, s2)
