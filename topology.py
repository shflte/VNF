from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
import json


if __name__ == "__main__":
    topo_file = "topology.json"
    net = Mininet(controller=RemoteController, link=TCLink)
    controller = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    with open(topo_file, "r") as file:
        topology = json.load(file)

    hosts = {}
    switches = {}

    # Add hosts
    for host in topology["nodes"]["hosts"]:
        hosts[host["name"]] = net.addHost(
            host["name"], ip=host["ip"], mac=host["mac"]
        )

    # Add switches
    for switch in topology["nodes"]["switches"]:
        switches[switch] = net.addSwitch(switch)

    # Add links with ports
    for link in topology["links"]:
        node1 = link["node1"]
        port1 = link["port1"]
        node2 = link["node2"]
        port2 = link["port2"]

        if node1 in hosts:
            net.addLink(hosts[node1], switches[node2], port1=port1, port2=port2)
        elif node2 in hosts:
            net.addLink(switches[node1], hosts[node2], port1=port1, port2=port2)
        else:
            net.addLink(switches[node1], switches[node2], port1=port1, port2=port2)

    # Start the network
    net.start()
    net.staticArp()

    # Start CLI
    CLI(net)

    # Stop the network
    net.stop()
