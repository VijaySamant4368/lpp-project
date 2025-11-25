import osmnx as ox

CENTER = (28.6129, 77.2295)    # Delhi center
CENTER = (28.69826841750161, 77.20602400925607) #GTB
DIST_HIGHEST = 10_000
DIST_HIGH = 7000
DIST_MID = 3000
DIST_SMALL = 1000

USE_DIST = DIST_MID
FILE_NAME = "delhi_small_drive" if USE_DIST == DIST_SMALL else "delhi_medium_drive" if USE_DIST == DIST_MID else "delhi_high_drive" if USE_DIST == DIST_HIGH else "delhi_19km_drive" if USE_DIST == DIST_HIGHEST else "idk"

G = ox.graph_from_point(CENTER, dist=USE_DIST, network_type="drive", simplify=True)
try:
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
except:
    pass

print("Total nodes:", len(G.nodes))
print("Total edges:", len(G.edges))

ox.save_graphml(G, f"{FILE_NAME}.graphml")
print(f"Saved {FILE_NAME}.graphml")
