from scraping._Database import Database
import pandas as pd
from selenium import webdriver
import sys
import math
import sentence_splitter
import numpy as np
from multiprocessing import Pool
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
plaintext: dict[dict]
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
        "Konflikt": "assets/icons/bomb.png",
        "Staat": "assets/icons/state.png",
        "Millionenstadt": "assets/icons/city.png",
    }
    for c in categories.get(title, []):
        if c.split(" ")[0] in list(category_icons.keys()):
            return category_icons[c.split(" ")[0]]
    return None


def get_plaintext(args):
    i,t = args
    return (t.title, {
        "de": wtp.parse(
            re.sub(
                '<ref(\sname="[^"]+")?>[^<]+<\/ref>',
                " ",
                t.content.replace("<br />", "").replace("<br>", ""),
            )
        ).plain_text(),
        "en": wtp.parse(
            re.sub(
                '<ref(\sname="[^"]+")?>[^<]+<\/ref>',
                " ",
                t.content_en.replace("<br />", "").replace("<br>", ""),
            )
        ).plain_text(),
    })


def get_dataframes():
    global links, all_links, titles, articles, episodes, categories, translations, plaintext
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


def link_context(text, link: pd.Series):
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
            .replace(
                link.string, wikilink.text
            )
        )
    except:
        small_context = wikilink.text
    small_context = small_context.strip("\n")

    text: str = plaintext[link.parent][link.lang]
    text_index = text.find(small_context)
    if text_index == -1:
        text_index = text.find(wikilink.text)
    context = text[max(0, text_index - 600): min(len(text) - 1, text_index + 600)]
    text_index = context.find(wikilink.text)
    if text_index == -1:
        return ""
    context = text[max(0, text_index - 400): min(len(text) - 1, text_index + 400)]
    return context
    sentences = sentence_splitter.split_text_into_sentences(context, language=link.lang)
    context = " ".join([sent for sent in sentences[1:-1] if not sent.startswith("==") and not sent.endswith("==")])

    return context


def article_meta(args):
    global articles, links, episodes, translations
    t = pd.Series(args[1])
    meta = {}
    eps = episodes.loc[episodes["nr"].isin(t.episode.split(","))]
    meta["episodes"] = (
        t.title,
        [
            {"nr": ep.nr, "title": ep.title, "link": ast.literal_eval(ep.links)[0]}
            for i, ep in eps.iterrows()
        ]
    )
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
    global all_links, articles, plaintext
    a = pd.Series(dict(zip(("url", "parent"), args)))
    link = all_links.loc[
        np.logical_and(all_links["parent"] == a.parent, all_links["url"] == a.url)
    ].iloc[0]
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
    global articles, links
    meta = {"translations": translations}
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
    global edges, nodes, categories, links, all_links, titles, articles, translations, episodes, edges, nodes, meta
    get_dataframes()
    edges = get_edges()
    nodes = get_nodes()
    meta = get_metadata()

    with open("visualize/data/data.js", "w", encoding="utf-8") as f:
        f.write(
            "const DATA = " + json.dumps({"nodes": nodes, "edges": edges, "meta": meta})
        )
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
    )


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
        progress = [0]
        iterations = 3000
        with alive_bar(iterations, title="pre-loading network") as bar:
            while progress[-1] < iterations:
                progress.append(driver.execute_script("return progress;"))
                bar(progress[-1] - progress[-2])
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
    args = sys.argv[1:]
    if len(args) == 0:
        refresh_data()
        create_save()
    else:
        options = ["--data", "--preload"]
        for option in options:
            if option in args:
                {"--data": refresh_data, "--preload": create_save}[option]()
