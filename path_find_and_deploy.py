import json
import networkx as nx
import requests


def load_topology(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def build_graph(topology):
    graph = nx.Graph()
    for link in topology["links"]:
        graph.add_edge(
            link["node1"], link["node2"], port1=link["port1"], port2=link["port2"]
        )
    return graph


def deploy_flow(switch, in_port, out_port, src_mac, dst_mac):
    url = "http://127.0.0.1:8080/flow"
    match = {"in_port": in_port, "eth_src": src_mac, "eth_dst": dst_mac}

    data = {
        "switch": int(switch.replace("s", "")),
        "match": match,
        "actions": [{"port": out_port}],
    }
    print("url: ", url)
    print("data: ", data)

    response = requests.post(url, json=data)
    if response.status_code == 200:
        print(
            f"Deployed rule to switch {switch}: in_port {in_port} -> out_port {out_port}, match: {match}"
        )
    else:
        print(f"Failed to deploy rule to switch {switch}: {response.text}")


def path_find_and_deploy(graph, topology):
    hosts = topology["nodes"]["hosts"]
    host_info = {host["name"]: host for host in hosts}

    for src in hosts:
        for dst in hosts:
            if src["name"] == dst["name"]:
                continue

            path1 = nx.shortest_path(graph, source=src["name"], target=dst["name"])
            print(f"Path1 from {src['name']} to {dst['name']}: {path1}")

            for i in range(1, len(path1) - 1):
                current_node = path1[i]
                next_node = path1[i + 1]
                prev_node = path1[i - 1]

                if not current_node.startswith("s"):
                    continue

                switch = current_node
                in_port = graph[prev_node][current_node]["port2"]
                out_port = graph[current_node][next_node]["port1"]

                deploy_flow(
                    switch, in_port, out_port, src_mac=src["mac"], dst_mac=dst["mac"]
                )
                deploy_flow(
                    switch, out_port, in_port, src_mac=dst["mac"], dst_mac=src["mac"]
                )

            graph_copy = graph.copy()

            for i in range(len(path1) - 1):
                u, v = path1[i], path1[i + 1]
                if graph_copy.has_edge(u, v):
                    graph_copy[u][v]["weight"] = 1000

            path2 = nx.shortest_path(
                graph_copy, source=src["name"], target=dst["name"], weight="weight"
            )
            print(f"Path2 from {src['name']} to {dst['name']}: {path2}")

            for i in range(1, len(path2) - 1):
                current_node = path2[i]
                next_node = path2[i + 1]
                prev_node = path2[i - 1]

                if not current_node.startswith("s"):
                    continue

                switch = current_node
                in_port = graph[prev_node][current_node]["port2"]
                out_port = graph[current_node][next_node]["port1"]

                deploy_flow(
                    switch, in_port, out_port, src_mac=src["mac"], dst_mac=dst["mac"]
                )
                deploy_flow(
                    switch, out_port, in_port, src_mac=dst["mac"], dst_mac=src["mac"]
                )


if __name__ == "__main__":
    topology_file = "topology.json"
    topology = load_topology(topology_file)
    graph = build_graph(topology)
    path_find_and_deploy(graph, topology)
