from fastapi import HTTPException
import osmnx as ox

GRAPH_FILE = "delhi_10km_drive.graphml"

try:
    print("Loading cached graph...")
    G = ox.load_graphml(GRAPH_FILE)

    # Project to avoid scikit-learn dependency for nearest_nodes
    G_proj = ox.project_graph(G)

    print("Graph loaded:", len(G.nodes), "nodes,", len(G.edges), "edges")
except Exception as e:
    G = None
    G_proj = None
    print("Graph load failed:", e)


def place_to_node(place_text: str):
    """
    Geocode place text and snap to nearest node in PROJECTED graph.
    Returns (node_id, (lat, lon))
    """
    if G is None or G_proj is None:
        raise HTTPException(status_code=500, detail="Graph not loaded.")

    try:
        lat, lon = ox.geocode(place_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Geocoding failed for '{place_text}': {e}")

    try:
        # IMPORTANT: use projected graph here
        node = ox.distance.nearest_nodes(G_proj, lon, lat)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Nearest node lookup failed: {e}")

    return node, (lat, lon)


def nodes_to_coords(path):
    """
    Convert list of nodes to list of [lat, lon] for Leaflet/polyline.
    """
    return [[G.nodes[n]["y"], G.nodes[n]["x"]] for n in path]


def path_stats(path):
    """
    Compute distance (meters) and intersections (hops) for a path.
    Safe for MultiDiGraph.
    """
    dist_m = 0.0
    for u, v in zip(path[:-1], path[1:]):
        edge_dict = G.get_edge_data(u, v)
        data = min(edge_dict.values(), key=lambda d: d.get("length", 0))
        dist_m += data.get("length", 0)

    intersections = len(path) - 1
    return float(dist_m), intersections
