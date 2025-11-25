import networkx as nx
from itertools import islice

def shortest_distance(G, s, t, k=5):
    """
    Top-k paths by least total distance.
    For now uses NetworkX shortest_simple_paths with weight='length'.
    Later replace with PuLP LPP.
    """
    gen = nx.shortest_simple_paths(G, s, t, weight="length")
    return list(islice(gen, k))


def fewest_intersections(G, s, t, k=5):
    """
    Top-k paths by least intersections (hop count).
    """
    gen = nx.shortest_simple_paths(G, s, t)
    return list(islice(gen, k))
