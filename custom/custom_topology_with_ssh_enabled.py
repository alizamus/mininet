#!/usr/bin/python

"""
Create a network and start sshd(8) on each host.

While something like rshd(8) would be lighter and faster,
(and perfectly adequate on an in-machine network)
the advantage of running sshd is that scripts can work
unchanged on mininet and hardware.

In addition to providing ssh access to hosts, this example
demonstrates:

- creating a convenience function to construct networks
- connecting the host network to the root namespace
- running server processes (sshd in this case) on hosts
"""

import sys

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg
from mininet.node import Node
from mininet.topolib import TreeTopo
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import Controller
from mininet.log import setLogLevel, info
from mininet.node import CPULimitedHost
from mininet.util import dumpNodeConnections

from mininet.node import RemoteController

import csv

class MyTopo( Topo ):
  def __init__( self ):
    Topo.__init__( self )

    p1 = self.addHost( 'p1', ip='10.0.2.0' )
    p2 = self.addHost( 'p2', ip='10.0.2.1' )
    p3 = self.addHost( 'p3', ip='10.0.2.2' )
    p4 = self.addHost( 'p4', ip='10.0.2.3' )
    p5 = self.addHost( 'p5', ip='10.0.2.4' )

    s1 = self.addSwitch( 's1' )
    s2 = self.addSwitch( 's2' )
    s3 = self.addSwitch( 's3' )
    
    self.addLink( p1, s1 )
    self.addLink( p2, s2 )
    self.addLink( p3, s3 )
    self.addLink( s1, s2 )
    self.addLink( s1, s3 )
    #self.addLink( s2, s3 ) #having this line means we have loop
    self.addLink( s2, p4 )
    self.addLink( s2, p5 )

def connectToRootNS( network, switch, ip, routes ):
    """Connect hosts to root namespace via switch. Starts network.
      network: Mininet() network object
      switch: switch to connect to root namespace
      ip: IP address for root namespace node
      routes: host networks to route to"""
    # Create a node in root namespace and link to switch 0
    root = Node( 'root', inNamespace=False )
    intf = TCLink( root, switch ).intf1
    root.setIP( ip, intf=intf )
    # Start network that now includes link to root namespace
    network.start()
    # Add routes from root ns to hosts
    for route in routes:
        root.cmd( 'route add -net ' + route + ' dev ' + str( intf ) )

def sshd( network, cmd='/usr/sbin/sshd', opts='-D',
          ip='10.123.123.1/32', routes=None, switch=None ):
    """Start a network, connect it to root ns, and run sshd on all hosts.
       ip: root-eth0 IP address in root namespace (10.123.123.1/32)
       routes: Mininet host networks to route to (10.0/24)
       switch: Mininet switch to connect to root namespace (s1)"""
    if not switch:
        switch = network[ 's1' ]  # switch to use
    if not routes:
        routes = [ '10.0.0.0/32' ]
    connectToRootNS( network, switch, ip, routes )
    for host in network.hosts:
        host.cmd( cmd + ' ' + opts + '&' )
    print
    print "*** Hosts are running sshd at the following addresses:"
    print
    for host in network.hosts:
        print host.name, host.IP()
    print
    print "*** Type 'exit' or control-D to shut down network"
    CLI( network )
    for host in network.hosts:
        host.cmd( 'kill %' + cmd )
    network.stop()


if __name__ == '__main__':
    lg.setLogLevel( 'info')
    net = Mininet( topo=MyTopo(), link=TCLink, controller=RemoteController)
    cont=net.addController('r1', controller=RemoteController, ip='192.168.56.103',port=6633)
    cont.start()
    p1,p2,p3,p4,p5 = net.getNodeByName('p1', 'p2', 'p3', 'p4', 'p5') #change this line for adding each node

    #MAC address for each file(should add one entry by adding new host)    
    p1.setMAC(mac='00:00:00:01:02:00')
    p2.setMAC(mac='00:00:00:01:02:01')
    p3.setMAC(mac='00:00:00:01:02:02')
    p4.setMAC(mac='00:00:00:01:02:03')
    p5.setMAC(mac='00:00:00:01:02:04')
    
    #list of the host used for installing mac to ip mapping in each host staticly
    hosts = [p1, p2, p3, p4, p5]	
   
    for p in hosts:
	with open('/home/mininet/mininet_git/mininet/custom/staticmapping.csv', 'rb') as csvfile:
		mapping = csv.reader(csvfile, delimiter=';', quotechar='|')
		for row in mapping:
			p.setARP(row[1], row[2])
	

    opts = ' '.join( sys.argv[ 1: ] ) if len( sys.argv ) > 1 else (
        '-D -o UseDNS=no -u0' )
    sshd( net, opts=opts )
