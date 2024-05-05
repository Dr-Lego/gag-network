from scraping._Database import Database
import pandas as pd
import itertools
import random
import json

db = Database()

link_filter = """SELECT DISTINCT * FROM links WHERE url IN (
      SELECT DISTINCT url FROM links
      WHERE url IN (SELECT title FROM articles)
      GROUP BY url having count(url) <= 8)
    )"""

# episodes = pd.read_sql("SELECT * FROM episodes", con=db.conn)
# nodes = [{ "id": e["nr"], "label": e["nr"], "title": e["title"] } for i, e in episodes.iterrows()]
topics = pd.read_sql("SELECT * FROM articles", con=db.conn)
nodes = [{ "id": t["title"], "label": t["title"]} for i, t in topics.iterrows()]

articles = pd.read_sql("SELECT * FROM articles", con=db.conn)

links = pd.read_sql(link_filter, con=db.conn) # "SELECT * FROM links WHERE url IN (SELECT title FROM articles)"
get_episodes = lambda link: articles.loc[articles["title"] == link]

db.close()

edges = []
hashes = []
for i, a in links.iterrows():
    source = get_episodes(a.parent)
    target = get_episodes(a.url)
    combs = [({"title": s.title, "parent": s.episode}, {"title": t.title, "parent": t.episode}) for j, t in target.iterrows() for i, s in source.iterrows()]
    for s, t in combs:
        if s['parent'] != t['parent']:
            c = {"id": f"{s['title']}-{t['title']}-", "from": s['parent'], "to": t['parent'], "arrows": "to", "label": f"{a.parent} - {a.url}"}
            hashed = json.dumps(c, sort_keys=True)
            if hashed not in hashes:
                c["id"]+=str(random.randint(0, 999999))
                edges.append(c)
                hashes.append(hashed)


connected_nodes = list(itertools.chain.from_iterable([[e["from"], e["to"]] for e in edges]))
nodes = [n for n in nodes if n["id"] in connected_nodes]


with open("visualize/data.js", "w", encoding="utf-8") as f:
    f.write("const DATA = " + json.dumps({"nodes": nodes, "edges": edges}))
    f.close()    


