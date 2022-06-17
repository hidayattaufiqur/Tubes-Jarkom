#!/usr/bin/python3
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.node import Node
from mininet.topo import Topo
from mininet.log import setLogLevel
from subprocess import Popen, PIPE
import time
import os

class LinuxRouter( Node ):
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()


class NetworkTopo( Topo ):

	def build( self, **_opts ):

		# Add Host
		hA = self.addHost( 'hA', ip='192.168.4.2/29', defaultRoute='via 192.168.4.3')
		hB = self.addHost( 'hB', ip='192.168.4.34/29', defaultRoute='via 192.168.4.33')

		# Add Router
		R1 = self.addNode( 'R1', cls=LinuxRouter, ip='192.168.4.17/29' )
		R2 = self.addNode( 'R2', cls=LinuxRouter, ip='192.168.4.25/29' )
		R3 = self.addNode( 'R3', cls=LinuxRouter, ip='192.168.4.18/29' )
		R4 = self.addNode( 'R4', cls=LinuxRouter, ip='192.168.4.58/29' )

		opts0 = dict(bw=0.5, delay='1ms', loss=0, max_queue_size=10, use_htb=True)
		opts1 = dict(bw=1, delay='1ms', loss=0, max_queue_size=10, use_htb=True)

		# Add Link Router - Router
		self.addLink( R1, R3, cls=TCLink, **opts0, intfName1='R1-eth2', intfName2='R3-eth2', 
					params1={'ip': '192.168.4.17/29'},
					params2={'ip': '192.168.4.18/29'})
		self.addLink( R1, R4, cls=TCLink, **opts1, intfName1='R1-eth1', intfName2='R4-eth1', 
					params1={'ip': '192.168.4.57/29'},
					params2={'ip': '192.168.4.58/29'})
		self.addLink( R2, R4, cls=TCLink, **opts0, intfName1='R2-eth2', intfName2='R4-eth2', 
					params1={'ip': '192.168.4.25/29'},
					params2={'ip': '192.168.4.26/29'})
		self.addLink( R2, R3, cls=TCLink, **opts1, intfName1='R2-eth1', intfName2='R3-eth1', 
					params1={'ip': '192.168.4.49/29'},
					params2={'ip': '192.168.4.50/29'})

		# Add Link Host - Router
		self.addLink( hA, R1, cls=TCLink,  **opts1, intfName2='R1-eth0',
					params1={'ip': '192.168.4.2/29'},
					params2={'ip': '192.168.4.3/29'}) 
		self.addLink( hA, R2, cls=TCLink,  **opts1, intfName2='R2-eth0',
					params1={'ip': '192.168.4.9/29'},
					params2={'ip': '192.168.4.10/29'}) 
		self.addLink( hB, R3, cls=TCLink,  **opts1, intfName2='R3-eth0',
					params1={'ip': '192.168.4.34/29'},
					params2={'ip': '192.168.4.33/29'}) 
		self.addLink( hB, R4, cls=TCLink,  **opts1, intfName2='R4-eth0',
					params1={'ip': '192.168.4.42/29'},
					params2={'ip': '192.168.4.41/29'}) 


def run():
	net = Mininet(topo=NetworkTopo())
	net.start()
	
	# Static Routing Host A
	net['hA'].cmd("ip rule add from 192.168.4.2 table 1")
	net['hA'].cmd("ip rule add from 192.168.4.9 table 2")
	net['hA'].cmd("ip route add 192.168.4.0/29 dev hA-eth0 scope link table 1")
	net['hA'].cmd("ip route add default via 192.168.4.3 dev hA-eth0 table 1")
	net['hA'].cmd("ip route add 192.168.4.8/29 dev hA-eth1 scope link table 2")
	net['hA'].cmd("ip route add default via 192.168.4.10 dev hA-eth1 table 2")
	net['hA'].cmd("ip route add default scope global nexthop via 192.168.4.3 dev hA-eth0")

	# Static Routing Host B
	net['hB'].cmd("ip rule add from 192.168.4.34 table 1")
	net['hB'].cmd("ip rule add from 192.168.4.42 table 2")
	net['hB'].cmd("ip route add 192.168.4.32/29 dev hB-eth0 scope link table 1")
	net['hB'].cmd("ip route add default via 192.168.4.33 dev hB-eth0 table 1")
	net['hB'].cmd("ip route add 192.168.4.40/29 dev hB-eth1 scope link table 2")
	net['hB'].cmd("ip route add default via 192.168.4.41 dev hB-eth1 table 2")
	net['hB'].cmd("ip route add default scope global nexthop via 192.168.4.33 dev hB-eth0")
	net['hB'].cmd("ip route add default scope global nexthop via 192.168.4.41 dev hB-eth1")

	# Static Routing R1
	net['R1'].cmd("route add -net 192.168.4.8/29 gw 192.168.4.18")  # net 2
	net['R1'].cmd("route add -net 192.168.4.24/29 gw 192.168.4.58") # net 4
	net['R1'].cmd("route add -net 192.168.4.48/29 gw 192.168.4.18") # net 7
	net['R1'].cmd("route add -net 192.168.4.32/29 gw 192.168.4.18") # net 5
	net['R1'].cmd("route add -net 192.168.4.40/29 gw 192.168.4.58") # net 6
 
	# Static Routing R2
	net['R2'].cmd("route add -net 192.168.4.0/29 gw 192.168.4.50")  # net 1
	net['R2'].cmd("route add -net 192.168.4.16/29 gw 192.168.4.50") # net 3
	net['R2'].cmd("route add -net 192.168.4.32/29 gw 192.168.4.50") # net 5
	net['R2'].cmd("route add -net 192.168.4.40/29 gw 192.168.4.26") # net 6
	net['R2'].cmd("route add -net 192.168.4.56/29 gw 192.168.4.26") # net 8

	# Static Routing R3
	net['R3'].cmd("route add -net 192.168.4.0/29 gw 192.168.4.17")  # net 1
	net['R3'].cmd("route add -net 192.168.4.8/29 gw 192.168.4.49")  # net 2
	net['R3'].cmd("route add -net 192.168.4.24/29 gw 192.168.4.49") # net 4
	net['R3'].cmd("route add -net 192.168.4.40/29 gw 192.168.4.17") # net 6
	net['R3'].cmd("route add -net 192.168.4.56/29 gw 192.168.4.17") # net 8

	# Static Routing R4
	net['R4'].cmd("route add -net 192.168.4.0/29 gw 192.168.4.57")  # net 1
	net['R4'].cmd("route add -net 192.168.4.8/29 gw 192.168.4.25")  # net 2
	net['R4'].cmd("route add -net 192.168.4.16/29 gw 192.168.4.57") # net 3
	net['R4'].cmd("route add -net 192.168.4.32/29 gw 192.168.4.17") # net 5
	net['R4'].cmd("route add -net 192.168.4.48/29 gw 192.168.4.25") # net 7

	# set Iperf
	net['hB'].cmd("iperf -s &")

	# Generate .pcap
	net['hB'].cmd("tcpdump -w 1301204300_tubes.pcap &")

	net['hA'].cmd("iperf -c 192.168.4.34 -t 100 &")
	time.sleep(10)
	net['hA'].cmd("iperf -c 192.168.4.34")

	CLI(net)
	net.stop()


if '__main__' == __name__:
	os.system('mn -c')
	os.system('clear')
	setLogLevel('info')

	key = "net.mptcp.mptcp_enabled"
	value = 0
	p = Popen("sysctl -w %s=%s" %(key,value), shell=True, stdout=PIPE, stderr=PIPE)
	stdout, stderr = p.communicate()
	print("stdout=",stdout,"stderr=",stderr)

	run()


    
