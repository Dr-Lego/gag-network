from scraping._Database import Database
import pandas as pd
from collections import defaultdict
import argparse
from selenium import webdriver
import sys
import numpy as np
from multiprocessing import Pool, Manager
from selenium.webdriver.support.ui import WebDriverWait
import itertools
import json
import ast
import numpy as np
import wikitextparser as wtp
from alive_progress import alive_bar
import re


"""
Create nodes and edges of the network and pre-load the network.
"""


edges: list
nodes: list
categories: dict
links: pd.DataFrame
all_links: pd.DataFrame
titles: pd.DataFrame
articles: pd.DataFrame
translations: dict
episodes: pd.DataFrame
edges: list
nodes: list
meta: dict


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
        "Staat": "assets/icons/state.png",
        "Millionenstadt": "assets/icons/city.png"
    }
    for c in categories.get(title, []):
        if c.split(" ")[0] in list(category_icons.keys()):
            return category_icons[c.split(" ")[0]]
    return None


def get_dataframes():
    global links, all_links, titles, articles, episodes, categories, translations
    db = Database()
    link_filter = """SELECT DISTINCT {} FROM links WHERE url IN (
        SELECT DISTINCT url FROM links
        WHERE url IN (SELECT title FROM articles)
        GROUP BY url having count(url) <= 5000)"""

    links = pd.read_sql(link_filter.format("url, parent, lang"), con=db.conn)
    links = links.sort_values(links.columns.to_list()).drop_duplicates(
        links.columns.drop("lang"), keep="first"
    )
    all_links = pd.read_sql(link_filter.format("*"), con=db.conn)
    titles = pd.read_sql("SELECT DISTINCT title FROM articles", con=db.conn)
    articles = pd.read_sql("SELECT * FROM articles", con=db.conn)
    translations = pd.read_sql("SELECT DISTINCT title, title_en FROM articles", con=db.conn).set_index("title").to_dict("index")
    episodes = pd.read_sql("SELECT * FROM episodes", con=db.conn)
    categories_df = pd.read_sql(
        "SELECT DISTINCT url, parent FROM links WHERE url LIKE 'Kategorie:%'",
        con=db.conn,
    )
    categories = {}
    for i, a in categories_df.iterrows():
        categories[a.parent] = categories.get(a.parent, []) + [
            a.url.removeprefix("Kategorie:")
        ]

    db.close()


def get_edges() -> list:
    global links
    edges = []
    hash_data = []
    for i, a in links.iterrows():
        data = {
            "id": f"{a['parent']}-{a['url']}",
            "from": a["parent"],
            "to": a["url"],
            "arrows": "to",
        }
        hashed = json.dumps(
            {
                "id": f"{a['url']}-{a['parent']}",
                "from": a["url"],
                "to": a["parent"],
                "arrows": "to",
            },
            sort_keys=True,
        )
        if hashed not in hash_data:
            edges.append(data)
            hash_data.append(json.dumps(data, sort_keys=True))
        else:
            edges[hash_data.index(hashed)]["arrows"] = "to, from"

    return edges


def get_nodes() -> list:
    global edges, titles
    connected_nodes = list(
        itertools.chain.from_iterable([[e["from"], e["to"]] for e in edges])
    )
    nodes = [
        {"id": t["title"], "label": t["title"]}
        for i, t in titles.iterrows()
        if t["title"] in connected_nodes
    ]
    for i, n in enumerate(nodes):
        nodes[i]["size"] = max(10, 10 + connected_nodes.count(n["id"]) * 0.5)
        icon = get_icon(n["id"])
        if icon:
            nodes[i]["image"] = icon
            nodes[i]["shape"] = "circularImage"

    return nodes


def link_context(text, link):
    # get small context of link to find correct loaction in plaintext article
    wikitext = wtp.parse(text)
    link = wtp.parse(link).wikilinks[0]
    text = wikitext.plain_text(replace_wikilinks=False)
    try:
        text = (
            re.search(r"[^\]]{0,100}" + re.escape(link.string) + r"[^\[]{0,100}", text)
            .group()
            .replace(link.string, link.text if link.text else link.target)
        )
    except:
        text = link.text if link.text else link.target
    return text


def article_meta(args):
    global articles, links, episodes, translations
    t = pd.Series(args[1])
    meta = {}
    eps = episodes.loc[episodes["nr"].isin(t.episode.split(","))]
    meta["episodes"] = (t.title, [{"nr": ep.nr, "title": ep.title, "link": ast.literal_eval(ep.links)[0]} for i, ep in eps.iterrows()])
    meta["summary"] = (t.title, t.description)
    meta["thumbnail"] = (t.title, t.thumbnail)
    meta["text"] = (
        t.title,
        {
            "de": wtp.parse(
                re.sub(
                    "<ref>[^<]+</ref>",
                    " ",
                    t.content.replace("<br />", "").replace("<br>", ""),
                )
            ).plain_text(),
            "en": wtp.parse(
                re.sub(
                    "<ref>[^<]+</ref>",
                    " ",
                    t.content_en.replace("<br />", "").replace("<br>", ""),
                )
            ).plain_text(),
        },
    )
    return meta

def link_meta(args):
    global all_links, articles
    a = pd.Series(dict(zip(("url", "parent"), args)))
    link = all_links.loc[
        np.logical_and(
            all_links["parent"] == a.parent, all_links["url"] == a.url
        )
    ].iloc[0]
    r = (f"{a.parent} -> {a.url}", {
        "text": link.text,
        "context": link_context(
            articles.loc[articles["title"] == a.parent].iloc[0].content,
            link.wikitext,
        ),
        "lang": link.lang,
    })
    return r


def get_metadata() -> dict:
    global articles, links
    meta = {"translations": translations}
    print("Preparing article metadata...", end="\t")
    with Pool() as pool:
        _meta = pool.map(article_meta, articles.to_dict("index").items())
        pool.close()
    meta.update({k: dict([d[k] for d in _meta if k in d]) for k in set().union(*_meta)})
    del _meta
    print("Done")

    # link context
    print("Preparing link metadata...", end="\t")
    with Pool() as pool:
        meta.update({"links": dict(pool.map(link_meta, list(set([tuple(row) for row in links.values.tolist()]))))})
        pool.close()
    print("Done")
    
    return meta


def refresh_data():
    global edges, nodes, meta
    get_dataframes()
    edges = get_edges()
    nodes = get_nodes()
    meta = get_metadata()

    with open("visualize/data/data.js", "w", encoding="utf-8") as f:
        f.write(
            "const DATA = " + json.dumps({"nodes": nodes, "edges": edges, "meta": meta})
        )
        f.close()


class wait_for_stabilized(object):
    def __init__(self) -> None:
        pass

    def __call__(self, driver: webdriver.Chrome):
        return driver.execute_script("return stabilized;")


def create_save():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get("file:///home/raphael/PROGRAMMING/Projekte/GAG/visualize/_preload.html")
    try:
        print("Pre-loading network...", end="\t")
        stabilized = WebDriverWait(driver, 300).until(wait_for_stabilized())
        save = json.dumps(
            driver.execute_script("return exportNetwork();"),
            separators=(",", ":"),
            ensure_ascii=False,
        )
        with open("visualize/data/save.js", "w", encoding="utf-8") as f:
            f.write(f"const SAVE = {save};")
    finally:
        driver.quit()
    print("Done")


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0:
        refresh_data()
        create_save()
    else:
        options = ["--data", "--save"]
        for option in options:
            if option in args:
                {"--data": refresh_data, "--save": create_save}[option]()
