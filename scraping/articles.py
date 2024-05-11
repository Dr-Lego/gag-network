import bz2
import pandas as pd
import ast
from typing import Iterable, Literal
import itertools
import threading
import requests
import time
from alive_progress import alive_bar
import json
import xmltodict
import numpy as np
from bs4 import BeautifulSoup
import constants
from scraping._Wikidump import Wikidump
from scraping._Database import Database


wikidump_de = Wikidump(constants.WIKIDUMP_DE, constants.WIKIDUMP_DE_INDEX)


def in_english(articles:list) -> list[dict]:
    chunks = np.array_split([a[1].removeprefix("/wiki/") for a in articles], np.arange(0, len(articles), 50))[1:]
    r: list[dict] = []
    with alive_bar(len(chunks), title="fetching redirects + translations") as bar:
        for chunk in chunks:
            r.append(json.loads(requests.get(f"https://de.wikipedia.org/w/api.php?action=query&prop=langlinks&titles={'|'.join(chunk)}&lllang=en&formatversion=2&lllimit=max&format=json&redirects=").text)["query"])
            bar()
        
    pages = list(itertools.chain.from_iterable([chunk.get("pages", []) for chunk in r]))
    redirected = list(itertools.chain.from_iterable([chunk.get("redirects", []) for chunk in r]))
    
    translations = {page["title"]: page["langlinks"][0]["title"] for page in pages if "langlinks" in page}
    redirects = {page["from"]: page["to"] for page in redirected}
        
    return [translations, redirects]


def scrape_articles(
    db=Iterable, mode: Literal["update", "refresh"] = "refresh"
) -> None:
    global wikidump_de
    episodes = pd.read_sql("SELECT * FROM episodes", con=db[1])
    episodes[["topics", "links"]] = episodes[["topics", "links"]].map(ast.literal_eval)

    articles = list(zip(episodes["nr"], episodes["topics"]))
    articles = [[(ep[0], a) for a in ep[1]] for ep in articles]
    articles = list(itertools.chain.from_iterable(articles))

    if mode == "update":
        _keys = [
            "/wiki/" + k
            for k in pd.read_sql("SELECT * FROM articles", con=db[1])["key"].to_list()
        ]
        articles = list([a for a in articles if a[1] not in _keys])
        
    translations, redirects = in_english(articles)

    with alive_bar(len(articles), title=f"{mode.removesuffix('e')}ing articles") as bar:
        for i, episode in enumerate(articles):
            key = episode[1].removeprefix("/wiki/")
            key = redirects.get(key, key)
            nr = episode[0]
            try:
                page: dict = xmltodict.parse(wikidump_de.get_page(key.replace("_", " ")))["page"]
                if page.get("redirect", False):
                    page: dict = xmltodict.parse(
                        wikidump_de.get_page(page["redirect"]["@title"])
                    )["page"]
                page["text"] = page["revision"]["text"]["#text"]

                api_call: dict = json.loads(
                    requests.get(
                        "https://de.wikipedia.org/api/rest_v1/page/summary/" + key,
                        headers={"User-Agent": constants.USER_AGENT},
                    ).text
                )
                description, thumbnail = api_call.get("extract", ""), api_call.get(
                    "originalimage", {}
                ).get("source", "")

                db[0].execute(
                    f"INSERT INTO articles (key, title, id, episode, content, description, thumbnail) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        key,
                        page["title"],
                        page["id"],
                        nr,
                        page["text"],
                        description,
                        thumbnail,
                    ),
                )

                if i % 50 == 0:
                    db[1].commit()
                #print(f"{i+1}/{len(articles)}     {key}   {nr}")
                time.sleep(0.2)
            except Exception as e:
                with open("articles.log", "a") as f:
                    f.write(page["title"] + "\n" + str(e) + "\n\n\n")
                    f.close()
                print("\033[91m", f"{i+1}/{len(articles)}     {key}", "\033[0m")

            bar()


def refresh_articles(mode: Literal["update", "refresh"] = "refresh") -> pd.DataFrame:
    db = Database()
    if mode == "refresh":
        db.drop("articles")
    db.setup()

    scrape_articles((db.c, db.conn), mode=mode)

    db.close()
