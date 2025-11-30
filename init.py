import osmnx as ox
import networkx as nx

center_address = "Bengaluru, India"
USE_DIST = 2000

desired_types = {"primary", "secondary", "tertiary"}

G = ox.graph_from_address(
    center_address,
    dist=USE_DIST,
    network_type="drive",
    simplify=True
)

G_filtered = G.copy()

edges_to_remove = []
for u, v, k, data in G_filtered.edges(keys=True, data=True):
    hw = data.get("highway")
    if hw is None:
        edges_to_remove.append((u, v, k))
        continue

    hw_list = hw if isinstance(hw, list) else [hw]
    if not desired_types.intersection(hw_list):
        edges_to_remove.append((u, v, k))

G_filtered.remove_edges_from(edges_to_remove)
G_filtered.remove_nodes_from(list(nx.isolates(G_filtered)))

print("Nodes:", len(G_filtered.nodes))
print("Edges:", len(G_filtered.edges))

ox.save_graphml(G_filtered, "primary_secondary_tertiary_roads.graphml")
