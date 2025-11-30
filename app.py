from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import networkx as nx

# from distance import shortest_distance, fewest_intersections
# from utils import place_to_node, path_stats, nodes_to_coords, G
from suggestions import suggestion_names, name_to_node
from utils import compute_route, all_edges

K = 5

app = FastAPI(title="Delhi Route Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel

class RouteRequest(BaseModel):
    start: str
    end: str
    primary: bool = True
    secondary: bool = True
    tertiary: bool = True


@app.get("/")
def root():
    return {"status": "ok", "message": "Delhi Route Finder backend running"}

# # -------------------------
# # Suggestions endpoints
# # -------------------------
@app.get("/suggest")
def suggest(q: str = Query("", min_length=1), limit: int = 10):
    q = q.strip().lower()
    if not q:
        return {"suggestions": []}
    matches = [name for name in suggestion_names if name.startswith(q)]
    return {"suggestions": matches[:limit]}

@app.post("/get-route")
def get_route(req: RouteRequest):
    return compute_route(
        start_name=req.start,
        end_name=req.end,
        primary=req.primary,
        secondary=req.secondary,
        tertiary=req.tertiary
    )

@app.get("/get-full-graph")
def get_full_graph():
    return all_edges()


# @app.post("/resolve_name")
# def resolve_name(payload: dict):
#     name = payload.get("name", "").strip().lower()
#     if name not in name_to_node:
#         raise HTTPException(status_code=400, detail="Name not found.")
#     return {"node_id": name_to_node[name]}


# # -------------------------
# # Routes endpoint
# # -------------------------
# @app.post("/routes")
# def routes(req: RouteRequest):
#     if G is None:
#         raise HTTPException(status_code=500, detail="Graph not loaded on server.")

#     s_node, s_latlon = place_to_node(req.start)
#     t_node, t_latlon = place_to_node(req.end)

#     if not nx.has_path(G, s_node, t_node):
#         raise HTTPException(
#             status_code=400,
#             detail="No path found between these points inside the fixed Delhi area."
#         )

#     hop_paths = fewest_intersections(G, s_node, t_node, K)
#     dist_paths = shortest_distance(G, s_node, t_node, K)

#     def build_payload(paths):
#         out = []
#         for p in paths:
#             dist_m, inters = path_stats(p)
#             out.append({
#                 "coords": nodes_to_coords(p),
#                 "distance_m": dist_m,
#                 "intersections": inters
#             })
#         return out

#     payload = {
#         "start": list(s_latlon),
#         "end": list(t_latlon),
#         "min_intersections": build_payload(hop_paths),
#         "min_distance": build_payload(dist_paths)
#     }

#     return JSONResponse(payload)


# # -------------------------
# # Show roads by osmids
# # -------------------------
# def edge_data_to_polyline(G, u, v, data):
#     geom = data.get("geometry")
#     if geom is not None:
#         return [[lat, lon] for lon, lat in geom.coords]
#     return [
#         [G.nodes[u]["y"], G.nodes[u]["x"]],
#         [G.nodes[v]["y"], G.nodes[v]["x"]],
#     ]

# @app.post("/show_roads")
# def show_roads(payload: dict = Body(...)):
#     if G is None:
#         raise HTTPException(status_code=500, detail="Graph not loaded on server.")

#     edges = payload.get("edges")
#     if not edges or not isinstance(edges, list):
#         raise HTTPException(status_code=400, detail="Payload must contain 'edges' list of [u,v,k].")

#     polylines = []
#     missing = []

#     for item in edges:
#         # validate shape: [u, v, k]
#         if not (isinstance(item, (list, tuple)) and len(item) == 3):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Each edge must be a 3-item list/tuple: [u, v, k]."
#             )

#         u, v, k = item
#         try:
#             # make sure types match graph keys (usually ints)
#             u = int(u)
#             v = int(v)
#             k = int(k)

#             data = G.edges[u, v, k]
#         except Exception:
#             missing.append([u, v, k])
#             continue

#         polylines.append(edge_data_to_polyline(G, u, v, data))

#     if missing:
#         # not fatal, but useful for debugging
#         return {"polylines": polylines, "missing_edges": missing}

#     return {"polylines": polylines}
