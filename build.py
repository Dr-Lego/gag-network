"""
Network Creation and Data Processing Script

This script creates nodes and edges of a network, pre-loads the network,
and processes data from various sources including databases and web feeds.
"""

import sys
import re
import json
import ast
import urllib.request
from multiprocessing import Pool
import itertools

import numpy as np
import pandas as pd
import podcastparser
import wikitextparser as wtp
import sentence_splitter
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from alive_progress import alive_bar

from scraping._Database import Database

# Global variables
edges = []
nodes = []
categories = {}
links = pd.DataFrame()
all_links = pd.DataFrame()
titles = pd.DataFrame()
articles = pd.DataFrame()
plaintext = {}
translations = {}
episodes = pd.DataFrame()
meta = {}
episode_covers = {}


def get_icon(title: str) -> str:
    """
    Retrieves the appropriate icon for the given category title.

    Args:
        title (str): The category title.

    Returns:
        str: The path to the icon file, or None if not found.
    """
    global categories
    category_icons = {
        "Person": "assets/icons/person.png",
        "Frau": "assets/icons/person.png",
        "Mann": "assets/icons/person.png",
        "Krieg": "assets/icons/explosion.png",
        "Konflikt": "assets/icons/explosion.png",
        "Staat": "assets/icons/state.png",
        "Königreich": "assets/icons/state.png",
        "Millionenstadt": "assets/icons/city.png",
    }
    for c in categories.get(title, []):
        if c.split(" ")[0] in list(category_icons.keys()):
            return category_icons[c.split(" ")[0]]
    return None


def get_plaintext(args):
    """
    Extracts plain text content from article data.

    Args:
        args (tuple): A tuple containing the index and article data.

    Returns:
        tuple: A tuple containing the article title and a dictionary of plain text content.
    """
    i, t = args
    return (
        t.title,
        {
            "de": wtp.parse(
                re.sub(
                    r"[^<]+<\/ref>",
                    " ",
                    t.content.replace("", "").replace("", ""),
                )
            ).plain_text(),
            "en": wtp.parse(
                re.sub(
                    r"[^<]+<\/ref>",
                    " ",
                    t.content_en.replace("", "").replace("", ""),
                )
            ).plain_text(),
        },
    )


def get_dataframes():
    """
    Retrieves data from the database and processes it into various DataFrames and dictionaries.
    """
    global links, all_links, titles, articles, episodes, categories, translations, plaintext, episode_covers
    db = Database()
    link_filter = """SELECT DISTINCT {} FROM links WHERE url IN (
        SELECT DISTINCT url FROM links
        WHERE url IN (SELECT title FROM articles)
        GROUP BY url having count(url) <= 5000)"""

    links = pd.read_sql(link_filter.format("url, parent, lang"), con=db.conn)
    links = links.sort_values(
        ["lang"], ascending=True
    ).drop_duplicates(  # links.columns.to_list()
        ["url", "parent"], keep="first"
    )
    all_links = pd.read_sql(link_filter.format("*"), con=db.conn)
    titles = pd.read_sql("SELECT DISTINCT title FROM articles", con=db.conn)
    articles = pd.read_sql("SELECT * FROM articles", con=db.conn)
    plaintext = []
    with Pool() as pool:
        with alive_bar(len(articles.index), title="getting plaintext articles") as bar:
            for _ in pool.imap_unordered(get_plaintext, articles.iterrows()):
                plaintext.append(_)
                bar()
    plaintext = dict(plaintext)
    translations = dict(
        pd.read_sql("SELECT DISTINCT title, title_en FROM articles", con=db.conn).values
    )
    episodes = pd.read_sql("SELECT * FROM episodes", con=db.conn)
    feed = podcastparser.parse(
        "https://geschichten-aus-der-geschichte.podigee.io/feed/mp3",
        urllib.request.urlopen(
            "https://geschichten-aus-der-geschichte.podigee.io/feed/mp3"
        ),
    )
    episode_covers = {
        ep["link"]
        .removesuffix("/")
        .split("/")[-1]: ep.get("episode_art_url", feed["cover_url"])
        .split("=/")[-1]
        for ep in feed["episodes"]
    }
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
    """
    Generates edges for the network based on link data.

    Returns:
        list: A list of edge dictionaries.
    """
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
    """
    Generates nodes for the network based on title data and connected nodes.

    Returns:
        list: A list of node dictionaries.
    """
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


def link_context(text, link: pd.Series):
    """
    Extracts context for a given link within an article's text.

    Args:
        text (str): The article text.
        link (pd.Series): A series containing link information.

    Returns:
        str: The extracted context or "Vorschau nicht verfügbar" if not found.
    """
    global plaintext
    # get small context of link to find correct location in plaintext article
    wikitext = wtp.parse(text).plain_text(replace_wikilinks=False)
    wikilink = wtp.parse(link.wikitext).wikilinks[0]
    if not wikilink.text:
        wikilink.text = wikilink.target
    try:
        small_context = (
            re.search(
                r"[^\]}]{0,100}" + re.escape(link.string) + r"[^\[{]{0,100}", wikitext
            )
            .group()
            .replace(link.string, wikilink.text)
        )
    except:
        small_context = wikilink.text
    small_context = small_context.strip("\n")

    text: str = plaintext[link.parent][link.lang]
    text_index = text.find(small_context)
    if text_index == -1:
        text_index = text.find(wikilink.text)
    context = text[max(0, text_index - 600) : min(len(text) - 1, text_index + 600)]
    text_index = context.find(wikilink.text)
    if text_index == -1:
        return "<br><span class='not-available'>Vorschau nicht verfügbar</span><br>"
    context = context[max(0, text_index - 400) : min(len(text) - 1, text_index + 400)]

    sentences = sentence_splitter.split_text_into_sentences(context, language=link.lang)
    if len(sentences) > 2:
        sentences = (
            [["", sentences[0]][wikilink.text in sentences[0]]]
            + sentences[1:-1]
            + [["", sentences[-1]][wikilink.text in sentences[-1]]]
        )
    elif len(sentences) == 0:
        return "<br><span class='not-available'>Vorschau nicht verfügbar</span><br>"

    context = " ".join(
        [
            sent
            for sent in sentences
            if not sent.startswith("==") and not sent.endswith("==")
        ]
    )
    if len(sentences) <= 2 and len(sentences) > 0:
        context = f"…{context}…"

    return context


def article_meta(args):
    """
    Extracts metadata for an article.

    Args:
        args (tuple): A tuple containing article data.

    Returns:
        dict: A dictionary of article metadata.
    """
    global articles, links, episodes, translations
    global articles, links, episodes, translations
    t = pd.Series(args[1])
    meta = {}
    eps = episodes.loc[episodes["nr"].isin(t.episode.split(","))]
    meta["episodes"] = (
        t.title,
        [
            {"nr": ep.nr, "title": ep.title, "link": ast.literal_eval(ep.links)[0]}
            for i, ep in eps.iterrows()
        ],
    )
    meta["summary"] = (t.title, t.description)
    meta["thumbnail"] = (t.title, t.thumbnail)
    return meta


def link_meta(args):
    """
    Extracts metadata for a link.

    Args:
        args (tuple): A tuple containing link data.

    Returns:
        tuple: A tuple containing link identifier and metadata.
    """
    global all_links, articles, plaintext
    a = pd.Series(dict(zip(("url", "parent"), args)))
    link = (
        all_links.loc[
            np.logical_and(all_links["parent"] == a.parent, all_links["url"] == a.url)
        ]
        .sort_values(["lang"], ascending=True)
        .iloc[0]
    )

    r = (
        f"{a.parent} -> {a.url}",
        {
            "text": link.text,
            "context": link_context(
                articles.loc[articles["title"] == a.parent].iloc[0][
                    f"content{['', '_en'][link.lang == 'en']}"
                ],
                link,
            ),
            "lang": link.lang,
        },
    )

    return r


def get_metadata() -> dict:
    """
    Collects and processes metadata for articles and links.

    Returns:
        dict: A dictionary containing all metadata.
    """
    global articles, links, episode_covers
    meta = {"translations": translations, "episode_covers": episode_covers}
    _meta = []
    with Pool() as pool:
        with alive_bar(len(articles.index), title="preparing article metadata") as bar:
            for _ in pool.imap_unordered(
                article_meta, articles.to_dict("index").items()
            ):
                _meta.append(_)
                bar()
        pool.close()
    meta.update({k: dict([d[k] for d in _meta if k in d]) for k in set().union(*_meta)})
    del _meta

    # link context
    _links = list(set([tuple(row) for row in links.values.tolist()]))
    _meta = []
    with Pool() as pool:
        with alive_bar(len(_links), title="preparing link metadata") as bar:
            for _ in pool.imap_unordered(link_meta, _links):
                _meta.append(_)
                bar()
        meta.update({"links": dict(_meta)})
        pool.close()
    del _links, _meta

    return meta


def refresh_data():
    """
    Refreshes all data by fetching from the database and processing it.
    """
    global edges, nodes, categories, links, all_links, titles, articles, translations, episodes, edges, nodes, meta, plaintext
    get_dataframes()
    edges = get_edges()
    nodes = get_nodes()
    meta = get_metadata()

    with open("frontend/src/lib/data/data.js", "w", encoding="utf-8") as f:
        f.write(
            "const DATA = "
            + json.dumps({"nodes": nodes, "edges": edges}, separators=(",", ":"))
        )
        f.close()

    with open("frontend/src/lib/data/meta.js", "w", encoding="utf-8") as f:
        f.write("export const META = " + json.dumps(meta, separators=(",", ":")))
        f.close()

    # clean up memory
    del (
        edges,
        nodes,
        categories,
        links,
        all_links,
        titles,
        articles,
        translations,
        episodes,
        meta,
        plaintext,
    )


def compress_save(save: dict[str, list[dict]]) -> dict:
    """
    Compresses the save data for efficient storage.

    Args:
        save (dict): The save data to compress.

    Returns:
        dict: The compressed save data.
    """
    icons = {
        "assets/icons/person.png": 1,
        "assets/icons/explosion.png": 2,
        "assets/icons/state.png": 3,
        "assets/icons/city.png": 4,
    }

    nodes = [
        list(
            filter(
                None,
                [
                    node["id"],
                    node["size"],
                    node["x"],
                    node["y"],
                    icons.get(node.get("image", ""), None),
                ],
            )
        )
        for node in save["nodes"]
    ]
    ids = {node[0]: i + 1 for i, node in enumerate(nodes)}

    edges = [
        list(
            filter(
                None,
                [
                    ids[edge["from"]],
                    ids[edge["to"]],
                    1 if edge["arrows"] == "to" else None,
                ],
            )
        )
        for edge in save["edges"]
    ]

    return {"nodes": nodes, "edges": edges, "icons": {v: k for k, v in icons.items()}}


class wait_for_stabilized(object):
    """A custom wait condition for Selenium WebDriver."""

    def __init__(self) -> None:
        pass

    def __call__(self, driver: webdriver.Chrome):
        return driver.execute_script("return stabilized;")


def create_save():
    """
    Creates and saves the network data for different sizes.
    """
    save = {}
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    for size, name in {1000: "full", 80: "small"}.items():
        driver.get(
           "file://" +  __file__.replace("build.py", f"frontend/_preload.html?exclude={size}")
        )
        progress = [0]
        iterations = 3000
        with alive_bar(iterations, title="pre-loading network") as bar:
            while progress[-1] < iterations:
                progress.append(driver.execute_script("return progress;"))
                bar(progress[-1] - progress[-2])
        stabilized = WebDriverWait(driver, 300).until(wait_for_stabilized())
        save[name] = compress_save(driver.execute_script("return exportNetwork();"))

    driver.quit()

    with open("frontend/src/lib/data/save.js", "w", encoding="utf-8") as f:
        f.write("export const SAVE = " + json.dumps(save, separators=(",", ":")))
        f.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0:
        refresh_data()
        create_save()
    else:
        options = ["--data", "--preload"]
        for option in options:
            if option in args:
                {"--data": refresh_data, "--preload": create_save}[option]()
