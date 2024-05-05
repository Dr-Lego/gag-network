from scraping._Database import Database
import pandas as pd
import itertools
import json
import wikitextparser as wtp

edges: list
nodes: list


def get_icon(title: str) -> str:
    global categories
    """
    Retrieves the appropriate icon for the given category title.
    """
    category_icons = {
        "Person": "assets/icons/person.png",
        "Frau": "assets/icons/person.png",
        "Mann": "assets/icons/person.png",
        "Krieg": "assets/icons/bomb.png",
        "Staat": "assets/icons/state.png"
    }
    for c in categories.get(title, []):
        if c.split(" ")[0] in list(category_icons.keys()):
            return category_icons[c.split(" ")[0]]
    return None


db = Database()
link_filter = """SELECT DISTINCT url, parent FROM links WHERE url IN (
      SELECT DISTINCT url FROM links
      WHERE url IN (SELECT title FROM articles)
      GROUP BY url having count(url) <= 1)"""

links = pd.read_sql(link_filter, con=db.conn)
titles = pd.read_sql("SELECT DISTINCT title FROM articles", con=db.conn)
articles = pd.read_sql("SELECT * FROM articles", con=db.conn)
episodes = pd.read_sql("SELECT * FROM episodes", con=db.conn)
categories_df = pd.read_sql("SELECT DISTINCT url, parent FROM links WHERE url LIKE 'Kategorie:%'", con=db.conn)
categories = {}
for i, a in categories_df.iterrows():
    categories[a.parent] = categories.get(a.parent, []) + [a.url.removeprefix("Kategorie:")]

db.close()


def get_edges() -> list:
    global links
    edges = []
    hash_data = []
    for i, a in links.iterrows():
        data = {"id": f"{a['parent']}-{a['url']}", "from": a['parent'], "to": a['url'], "arrows": "to"}
        hashed = json.dumps({"id": f"{a['url']}-{a['parent']}", "from": a['url'], "to": a['parent'], "arrows": "to"}, sort_keys=True)
        if hashed not in hash_data:
            edges.append(data)
            hash_data.append(json.dumps(data, sort_keys=True))
        else:
            edges[hash_data.index(hashed)]["arrows"] = "to, from"

    return edges


def get_nodes() -> list:
    global edges
    connected_nodes = list(itertools.chain.from_iterable([[e["from"], e["to"]] for e in edges]))
    nodes = [{"id": t["title"], "label": t["title"]} for i, t in titles.iterrows() if t["title"] in connected_nodes]
    for i, n in enumerate(nodes):
        nodes[i]["size"] = max(10, 10+connected_nodes.count(n["id"])*0.5)
        icon = get_icon(n["id"])
        if icon:
            nodes[i]["image"] = icon
            nodes[i]["shape"] = "circularImage"

    return nodes


def get_metadata() -> dict:
    meta = {"episodes": {}, "summary":{}, "thumbnail": {}}
    for i, t in articles.iterrows():
        meta["episodes"][t.title] = meta["episodes"].get(t.title, []) + [{k:list(v.values())[0] for k, v in episodes.loc[episodes["nr"] == t.episode].to_dict().items()}]
        meta["summary"][t.title] = t.description
        meta["thumbnail"][t.title] = t.thumbnail
    return meta

edges = get_edges()
nodes = get_nodes()
meta = get_metadata()


with open("visualize/data/data.js", "w", encoding="utf-8") as f:
    f.write("const DATA = " + json.dumps({"nodes": nodes, "edges": edges, "meta": meta}))
    f.close()    


