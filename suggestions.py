import json

NODE_JSON_BNGL = "node_primary_secondary_tertiary.json"

def normalize_address(addr: str) -> str:
    if not addr:
        return ""
    short = addr.split(",")[0].strip().lower()
    return short

print("Loading node.json for suggestions...")
with open(NODE_JSON_BNGL, "r", encoding="utf-8") as f:
    node_map = json.load(f)

name_to_node_bngl = {}
for node_id_str, addr in node_map.items():
    name = normalize_address(addr)
    if not name:
        continue
    
    if name not in name_to_node_bngl:
        name_to_node_bngl[name] = int(node_id_str)

suggestion_names_bngl = sorted(name_to_node_bngl.keys())

print("Loaded distinct names:", len(suggestion_names_bngl))

NODE_JSON_DLH = "node_vv.json"

def normalize_address(addr: str) -> str:
    if not addr:
        return ""
    short = addr.split(",")[0].strip().lower()
    return short

print("Loading node.json for suggestions...")
with open(NODE_JSON_DLH, "r", encoding="utf-8") as f:
    node_map = json.load(f)

name_to_node_dlh = {}
for node_id_str, addr in node_map.items():
    name = normalize_address(addr)
    if not name:
        continue
    
    if name not in name_to_node_dlh:
        name_to_node_dlh[name] = int(node_id_str)

suggestion_names_dlh = sorted(name_to_node_dlh.keys())

print("Loaded distinct names:", len(suggestion_names_dlh))