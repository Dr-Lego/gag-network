from scraping._Database import Database
import pandas as pd
import argparse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import itertools
import json
import json
import numpy as np
import wikitextparser as wtp
from alive_progress import alive_bar
import re

edges: list
nodes: list
categories: dict
links: pd.DataFrame
link_texts: pd.DataFrame
titles: pd.DataFrame
articles: pd.DataFrame
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
    }
    for c in categories.get(title, []):
        if c.split(" ")[0] in list(category_icons.keys()):
            return category_icons[c.split(" ")[0]]
    return None


def get_dataframes():
    global links, link_texts, titles, articles, episodes, categories
    db = Database()
    link_filter = """SELECT DISTINCT url, parent FROM links WHERE url IN (
        SELECT DISTINCT url FROM links
        WHERE url IN (SELECT title FROM articles)
        GROUP BY url having count(url) <= 50)"""

    links = pd.read_sql(link_filter, con=db.conn)
    links = links.sort_values(links.columns.to_list()).drop_duplicates(
        links.columns.drop("lang"), keep="first"
    )
    link_texts = pd.read_sql("SELECT * FROM links", con=db.conn)
    titles = pd.read_sql("SELECT DISTINCT title FROM articles", con=db.conn)
    articles = pd.read_sql("SELECT * FROM articles", con=db.conn)
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


def get_metadata() -> dict:
    global articles, links
    meta = {"episodes": {}, "summary": {}, "thumbnail": {}, "text": {}, "links": {}, "lang": {}}
    with alive_bar(len(articles.index), title="preparing article metadata") as bar:
        for i, t in articles.iterrows():
            meta["episodes"][t.title] = meta["episodes"].get(t.title, []) + [
                {
                    k: list(v.values())[0]
                    for k, v in episodes.loc[episodes["nr"] == t.episode]
                    .to_dict()
                    .items()
                }
            ]
            meta["summary"][t.title] = t.description
            meta["thumbnail"][t.title] = t.thumbnail
            meta["text"][t.title] = {
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
                ).plain_text()
            }
            bar()

    # link context
    with alive_bar(len(links.index), title="preparing link metadata") as bar:
        for i, a in links.iterrows():
            if f"{a.parent} -> {a.url}" not in meta["links"]:
                link = link_texts.loc[
                    np.logical_and(
                        link_texts["parent"] == a.parent, link_texts["url"] == a.url
                    )
                ].iloc[0]
                meta["links"][f"{a.parent} -> {a.url}"] = {
                    "text": link.text,
                    "context": link_context(
                        articles.loc[articles["title"] == a.parent].iloc[0].content,
                        link.wikitext,
                    ),
                }
                bar()
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
    driver.get("file:///home/raphael/PROGRAMMING/Projekte/GAG/save/prepare.html")
    try:
        print(
            "Please be patient while a save is being created. This can take up to a few minutes."
        )
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        help="nodes and edges are refreshed",
        default=True,
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--save",
        help="a new network save is created",
        default=True,
        action=argparse.BooleanOptionalAction,
    )
    args = parser.parse_args()
    if args.data:
        refresh_data()
    if args.save:
        create_save()
