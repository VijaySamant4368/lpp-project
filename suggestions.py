import json

NODE_JSON = "node_primary_secondary_tertiary.json"

def normalize_address(addr: str) -> str:
    """
    Extract a short searchable name from full address.
    For example:
    'Nelson Mandela Marg, Vasant Kunj, New Delhi, India'
        → 'nelson mandela marg'
    """
    if not addr:
        return ""
    short = addr.split(",")[0].strip().lower()
    return short


print("Loading node.json for suggestions...")
with open(NODE_JSON, "r", encoding="utf-8") as f:
    node_map = json.load(f)

name_to_node = {}
for node_id_str, addr in node_map.items():
    name = normalize_address(addr)
    if not name:
        continue
    
    if name not in name_to_node:
        name_to_node[name] = int(node_id_str)

suggestion_names = sorted(name_to_node.keys())

print("Loaded distinct names:", len(suggestion_names))
