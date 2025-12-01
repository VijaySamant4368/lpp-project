from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from suggestions import suggestion_names_bngl, suggestion_names_dlh
from utils import compute_route, all_edges

K = 5

app = FastAPI(title="Delhi & Bangalore Route Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RouteRequest(BaseModel):
    start: str
    end: str
    primary: bool = True
    secondary: bool = True
    tertiary: bool = True
    city: str = "bangalore"


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Route Finder backend running",
        "cities": ["bangalore", "delhi"],
    }


@app.get("/suggest")
def suggest(
    q: str = Query("", min_length=1),
    limit: int = 10,
    city: str = Query("bangalore")
):
    """
    Autocomplete suggestions for a city.
    city: "bangalore" or "delhi"
    """
    q = q.strip().lower()
    if not q:
        return {"suggestions": []}

    city_norm = city.strip().lower()

    if city_norm in ("delhi", "dlh", "new delhi"):
        source = suggestion_names_dlh
    else:
        source = suggestion_names_bngl

    matches = [name for name in source if name.startswith(q)]
    return {"suggestions": matches[:limit]}


@app.post("/get-route")
def get_route(req: RouteRequest):
    """
    Compute route in the selected city's graph.
    """
    city_norm = req.city.strip().lower()
    print(city_norm)

    return compute_route(
        start_name=req.start,
        end_name=req.end,
        primary=req.primary,
        secondary=req.secondary,
        tertiary=req.tertiary,
        city=city_norm,
    )


@app.get("/get-full-graph")
def get_full_graph(city: str = Query("bangalore")):
    """
    Return full road network for the selected city.
    """
    city_norm = city.strip().lower()
    print(city_norm)
    return all_edges(city=city_norm)
