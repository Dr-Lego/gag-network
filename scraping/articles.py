import pandas as pd
import ast
from typing import Literal, IO
import itertools
from bs4 import BeautifulSoup
from multiprocessing import Pool
import functools
import requests
from bz2 import BZ2Decompressor
from werkzeug.datastructures import MultiDict
import sqlite3
from alive_progress import alive_bar
import json
import urllib.parse
import xmltodict
import numpy as np
import constants
from scraping._Database import Database
from scraping._Index import Index

index_de: Index
index_en: Index

def foo(f):
    """Execute a function and return its result."""
    return f()

def none(*args):
    """Return None regardless of input."""
    return None

def make_request(titles):
    """Make an API request to Wikipedia for language links."""
    return json.loads(requests.get(
        f"https://de.wikipedia.org/w/api.php?action=query&prop=langlinks&titles={'|'.join(titles)}&lllang=en&formatversion=2&lllimit=max&format=json&redirects="
    ).text)["query"]

def in_english(articles: list) -> list[dict]:
    """Get English translations and redirects for given articles."""
    # Split articles into chunks and make API requests
    chunks = np.array_split(
        [urllib.parse.quote_plus(a[1].replace(" ", "_")) for a in articles],
        np.arange(0, len(articles), 50),
    )[1:]
    r: list[dict] = []
    with Pool() as pool:
        with alive_bar(len(chunks), title="fetching redirects and translations") as bar:
            for _ in pool.imap_unordered(make_request, chunks):
                r.append(_)
                bar()

    # Process API responses
    pages = list(itertools.chain.from_iterable([chunk.get("pages", []) for chunk in r]))
    redirected = list(
        itertools.chain.from_iterable([chunk.get("redirects", []) for chunk in r])
    )

    translations = {
        page["title"]: page["langlinks"][0]["title"]
        for page in pages
        if "langlinks" in page
    }
    redirects = {page["from"]: page["to"] for page in redirected}

    return [translations, redirects]

def get_page(path: str, title: str, start_byte: int, end_byte: int):
    """Retrieve and parse a page from a Wikipedia dump file."""
    with open(path, "rb") as file:
        file.seek(start_byte)
        readback = file.read(end_byte - start_byte - 1)
        file.close()
    page_xml = BZ2Decompressor().decompress(readback).decode()
    soup = BeautifulSoup(page_xml, "lxml")
    page = soup.find("title", string=title).parent
    return xmltodict.parse(str(page))["page"]

def api_call(title: str):
    """Make an API call to Wikipedia's REST API for page summary."""
    r = json.loads(
        requests.get(
            "https://de.wikipedia.org/api/rest_v1/page/summary/" + title,
            headers={"User-Agent": constants.USER_AGENT},
        ).text
    )
    return r

def scrape_articles(
    db=tuple[sqlite3.Cursor, sqlite3.Connection],
    mode: Literal["update", "refresh"] = "refresh",
) -> None:
    """Scrape articles from Wikipedia and store them in the database."""
    global index_de, index_en

    # Fetch episodes from the database
    episodes = pd.read_sql("SELECT * FROM episodes", con=db[1])
    episodes[["topics", "links"]] = episodes[["topics", "links"]].map(ast.literal_eval)

    # Prepare list of articles to scrape
    articles = list(zip(episodes["nr"], episodes["topics"]))
    articles = [[(ep[0], a) for a in ep[1]] for ep in articles]
    articles = list(itertools.chain.from_iterable(articles))

    if mode == "update":
        # Filter out articles already in the database
        _keys = [
            "/wiki/" + k
            for k in pd.read_sql("SELECT * FROM articles", con=db[1])["key"].to_list()
        ]
        articles = list([a for a in articles if a[1] not in _keys])

    # Get English translations and redirects
    translations, redirects = in_english(articles)

    original_articles = {redirects.get(title, title): title for nr, title in articles}
    episodes_dict: MultiDict = MultiDict(
        [(redirects.get(title, title), nr) for nr, title in articles]
    )
    articles = [redirects.get(title, title) for nr, title in articles]

    # Fetch article indexes
    index: dict[str, pd.DataFrame] = {
        "de": pd.read_sql(
            f"SELECT * FROM pages WHERE title IN {tuple(set([title for title in articles]))}",
            index_de.conn,
        ),
        "en": pd.read_sql(
            f"SELECT * FROM pages WHERE title IN {tuple(filter(None, set([translations.get(title, '') for title in articles])))}",
            index_en.conn,
        ),
    }
    for iterations in index.values():
        iterations.set_index("id", inplace=True)
        iterations.sort_values("start")

    wikidump_de: IO = open(constants.WIKIDUMP_DE, "rb")
    wikidump_en: IO = open(constants.WIKIDUMP_EN, "rb")

    # Scrape and process articles
    with alive_bar(len(index["de"].index), title=f"refreshing articles") as bar:
        iterations = 0
        for id, row in index["de"].iterrows():
            row_en = index["en"].loc[
                index["en"].title == translations.get(row.title, "")
            ]
            if not row_en.empty:
                row_en = row_en.iloc[0]

            # Prepare processes for parallel execution
            processes: dict[str, functools.partial] = {
                "de": functools.partial(
                    get_page,
                    *(
                        constants.WIKIDUMP_DE,
                        row.title,
                        row.start,
                        row.end,
                    ),
                ),
                "en": (
                    functools.partial(
                        get_page,
                        *(
                            constants.WIKIDUMP_EN,
                            row_en.title,
                            row_en.start,
                            row_en.end,
                        ),
                    )
                    if not row_en.empty
                    else functools.partial(none)
                ),
                "api": functools.partial(api_call, row.title),
            }

            # Execute processes in parallel
            page: list
            with Pool() as pool:
                page = pool.map(foo, processes.values())
                pool.close()

            page: dict = dict(zip(("de", "en", "api"), page))
            if not page["en"]:
                del page["en"]

            # Insert article data into the database
            db[0].execute(
                f"INSERT INTO articles (key, title, title_en, id, episode, content, content_en, description, thumbnail) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    original_articles[row.title],
                    row.title,
                    row_en.title if not row_en.empty else "",
                    id,
                    ",".join(episodes_dict.getlist(row.title)),
                    page["de"]["revision"]["text"]["#text"],
                    page["en"]["revision"]["text"]["#text"] if "en" in page else "",
                    page["api"].get("extract", ""),
                    page["api"].get("originalimage", {}).get("source", ""),
                ),
            )

            if iterations % 50 == 0:
                db[1].commit()

            bar()
            iterations += 1

    db[1].commit()

    wikidump_de.close()
    wikidump_en.close()

def refresh_articles(mode: Literal["update", "refresh"] = "refresh") -> pd.DataFrame:
    """Refresh or update articles in the database."""
    global index_en, index_de
    index_de = Index(constants.WIKIDUMP_DE_INDEX)
    index_en = Index(constants.WIKIDUMP_EN_INDEX)
    db = Database()

    if mode == "refresh":
        db.drop("articles")
    db.setup()

    scrape_articles((db.c, db.conn), mode=mode)

    db.close()
    index_de.close()
    index_en.close()