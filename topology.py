from mininet.topo import Topo
import json


class CustomTopo(Topo):
    def __init__(self, topo_file):
        Topo.__init__(self)
        self.load_topology(topo_file)

    def load_topology(self, topo_file):
        with open(topo_file, "r") as file:
            topology = json.load(file)

        hosts = {}
        switches = {}

        # Add hosts
        for host in topology["nodes"]["hosts"]:
            hosts[host["name"]] = self.addHost(
                host["name"], ip=host["ip"], mac=host["mac"]
            )

        # Add switches
        for switch in topology["nodes"]["switches"]:
            switches[switch] = self.addSwitch(switch)

        # Add links with ports
        for link in topology["links"]:
            node1 = link["node1"]
            port1 = link["port1"]
            node2 = link["node2"]
            port2 = link["port2"]

            if node1 in hosts:
                self.addLink(hosts[node1], switches[node2], port1=port1, port2=port2)
            elif node2 in hosts:
                self.addLink(switches[node1], hosts[node2], port1=port1, port2=port2)
            else:
                self.addLink(switches[node1], switches[node2], port1=port1, port2=port2)


topos = {"custom": (lambda: CustomTopo("topology.json"))}
