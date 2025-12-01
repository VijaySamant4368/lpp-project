from fastapi import HTTPException
import osmnx as ox
from suggestions import name_to_node_bngl, name_to_node_dlh
import pulp as lp

GRAPH_FILE_BNGL = "primary_secondary_tertiary_roads.graphml"
GRAPH_FILE_DLH = "vv.graphml"

try:
    print("Loading cached graph...")
    G_DLH = ox.load_graphml(GRAPH_FILE_DLH)
    G_BNGL = ox.load_graphml(GRAPH_FILE_BNGL)

    print("Graphs loaded")
except Exception as e:
    G = None
    print("Graph load failed:", e)

def shortest_distance_lpp_with_osmids(
    G,
    s,
    t,
    primary_preferred: bool = True,
    secondary_preferred: bool = True,
    tertiary_preferred: bool = True
):
    def get_multiplier(highway_tag):
        if not highway_tag:
            return 1.0
        h = str(highway_tag).lower()

        is_primary   = h in ("primary", "primary_link")
        is_secondary = h in ("secondary", "secondary_link")
        is_tertiary  = h in ("tertiary", "tertiary_link", "unclassified", "residential", "living_street", "road")

        pref_count = sum([primary_preferred, secondary_preferred, tertiary_preferred])

        if pref_count == 3:  # all allowed → normal
            return 1.0
        if pref_count == 0:
            return 1.0

        # Exactly 1 preferred → strong bonus + huge penalty
        if pref_count == 1:
            if (primary_preferred and is_primary) or \
               (secondary_preferred and is_secondary) or \
               (tertiary_preferred and is_tertiary):
                return 0.90  # small speed bonus
            else:
                return 3.8   # avoid like fire

        # Exactly 2 preferred
        if pref_count == 2:
            if (is_primary and not primary_preferred) or \
               (is_secondary and not secondary_preferred) or \
               (is_tertiary and not tertiary_preferred):
                return 3.0   # strong penalty
            else:
                return 1.0

        return 1.0  # fallback

    edges_cost = {}
    best_key = {}
    for u, v, k, data in G.edges(keys=True, data=True):
        length = float(data.get("length", 0.0))
        highway = data.get("highway", "")
        multiplier = get_multiplier(highway)

        cost = length * multiplier

        edge_pair = (u, v)
        if edge_pair not in edges_cost or cost < edges_cost[edge_pair]:
            edges_cost[edge_pair] = cost
            best_key[edge_pair] = k

    E = list(edges_cost.keys())

    # === ILP===
    problem = lp.LpProblem("ShortestPath", lp.LpMinimize)
    x = lp.LpVariable.dicts("x", E, 0, 1, cat=lp.LpBinary)

    problem += lp.lpSum(edges_cost[e] * x[e] for e in E)    #Sum up all the edges that are chosen(in x)

    nodes = list(G.nodes())
    for v in nodes:
        out_edges_from_v = [e for e in E if e[0] == v]
        in_edges_from_v = [e for e in E if e[1] == v]

        if v == s:
            problem += lp.lpSum(x[e] for e in out_edges_from_v) - lp.lpSum(x[e] for e in in_edges_from_v) == 1
        elif v == t:
            problem += lp.lpSum(x[e] for e in out_edges_from_v) - lp.lpSum(x[e] for e in in_edges_from_v) == -1
        else:
            problem += lp.lpSum(x[e] for e in out_edges_from_v) - lp.lpSum(x[e] for e in in_edges_from_v) == 0

    status = problem.solve(lp.PULP_CBC_CMD(msg=False))
    if lp.LpStatus[status] != "Optimal":
        raise ValueError("No optimal path found.")

    chosen = {(u, v) for (u, v) in E if lp.value(x[(u, v)]) > 0.5}

    # Reconstruct path
    node_path = [s]
    cur = s
    visited = {s}
    while cur != t:
        nxts = [v for (uu, v) in chosen if uu == cur]
        if not nxts:
            raise ValueError("Failed to reconstruct path.")
        nxt = nxts[0]
        if nxt in visited:
            raise ValueError("Cycle detected.")
        node_path.append(nxt)
        visited.add(nxt)
        cur = nxt

    edge_path_uv = list(zip(node_path[:-1], node_path[1:]))
    edge_path_uvk = [(u, v, best_key[(u, v)]) for (u, v) in edge_path_uv]

    # Extract OSMIDs
    edge_osmids = []
    for u, v, k in edge_path_uvk:
        data = G.get_edge_data(u, v, k)
        osmid = data.get("osmid")
        edge_osmids.append(int(osmid[0]) if isinstance(osmid, list) else int(osmid))

    # Total real distance (not weighted)
    total_real_distance = sum(
        G.edges[u, v, k]["length"]
        for u, v, k in edge_path_uvk
    )

    return node_path, edge_osmids, edge_path_uvk, total_real_distance

def compute_route(start_name: str, end_name: str, primary: bool = True, secondary: bool = True, tertiary: bool = True, city=""):
    G = G_DLH if city== "delhi" else G_BNGL
    name_to_node = name_to_node_dlh if city=="delhi" else name_to_node_bngl

    start_key = start_name.strip().lower()
    end_key = end_name.strip().lower()

    if start_key not in name_to_node:
        raise HTTPException(status_code=400, detail=f"Unknown start place: {start_name}")
    if end_key not in name_to_node:
        raise HTTPException(status_code=400, detail=f"Unknown end place: {end_name}")

    s = name_to_node[start_key]
    t = name_to_node[end_key]

    node_path, osmids, edge_path_uvk, total_dist = shortest_distance_lpp_with_osmids(
        G, s, t,
        primary_preferred=primary,
        secondary_preferred=secondary,
        tertiary_preferred=tertiary
    )

    polylines = []
    for (u, v, k) in edge_path_uvk:
        data = G.edges[u, v, k]
        geom = data.get("geometry")
        if geom is not None:
            poly = [[lat, lon] for lon, lat in geom.coords]
        else:
            poly = [
                [G.nodes[u]["y"], G.nodes[u]["x"]],
                [G.nodes[v]["y"], G.nodes[v]["x"]]
            ]
        polylines.append(poly)

    return {
        "start_name": start_name,
        "end_name": end_name,
        "start_node_id": s,
        "end_node_id": t,
        "distance_m": total_dist,
        "node_path": node_path,
        "edges": edge_path_uvk,
        "osmids": osmids,
        "polylines": polylines
    }

def all_edges(city):
    polylines = []
    G = G_DLH if city== "delhi" else G_BNGL

    for u, v, k, data in G.edges(keys=True, data=True):
        hw = data.get("highway")
        if hw is None:
            continue

        hw_list = hw if isinstance(hw, list) else [hw]
        road_type = (
            "primary" if "primary" in hw_list else
            "secondary" if "secondary" in hw_list else
            "tertiary" if "tertiary" in hw_list else None
        )
        if road_type is None:
            continue

        geom = data.get("geometry")
        if geom:
            coords = [[lat, lon] for lon, lat in geom.coords]
        else:
            coords = [
                [G.nodes[u]["y"], G.nodes[u]["x"]],
                [G.nodes[v]["y"], G.nodes[v]["x"]]
            ]

        polylines.append({
            "coords": coords,
            "type": road_type
        })

    return {"edges": polylines}