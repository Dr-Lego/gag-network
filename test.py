import json

def compress_save(data: str) -> dict:
    save: dict[str, list[dict]] = json.loads(data)
    icons = {
        "": None,
        "assets/icons/person.png": 1,
        "assets/icons/bomb.png": 2,
        "assets/icons/state.png": 3,
        "assets/icons/city.png": 4,
    }


    nodes = [list(filter(None, [node["id"], node["size"], node["x"], node["y"], icons[node.get("image", "")]])) for node in save["nodes"]]
    ids = {node[0]: i+1 for i, node in enumerate(nodes)}

    edges = [list(filter(None, [ids[edge["from"]], ids[edge["to"]], 1 if edge["arrows"] == "to" else None])) for edge in save["edges"]]
    
    return {"nodes": nodes, "edges": edges}

    with open("visualize/data/_save.js", "w", encoding="utf-8") as f:
        f.write("const SAVE = "+json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False))
        f.close()