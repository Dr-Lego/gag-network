import bz2
import pandas as pd
import ast
from typing import Iterable, Literal
import itertools
from multiprocessing import Process, Manager
import requests
import time
import sqlite3
from alive_progress import alive_bar
import json
import urllib.parse
import xmltodict
import numpy as np
import constants
from scraping._Wikidump import Wikidump
from scraping._Database import Database


wikidump_de: Wikidump = Wikidump(constants.WIKIDUMP_DE, constants.WIKIDUMP_DE_INDEX)
wikidump_en: Wikidump = Wikidump(constants.WIKIDUMP_EN, constants.WIKIDUMP_EN_INDEX)


def in_english(articles: list) -> list[dict]:
    chunks = np.array_split(
        [urllib.parse.quote_plus(a[1].replace(" ", "_")) for a in articles],
        np.arange(0, len(articles), 50),
    )[1:]
    r: list[dict] = []
    with alive_bar(len(chunks), title="fetching redirects + translations") as bar:
        for chunk in chunks:
            query = requests.get(
                f"https://de.wikipedia.org/w/api.php?action=query&prop=langlinks&titles={'|'.join(chunk)}&lllang=en&formatversion=2&lllimit=max&format=json&redirects="
            ).text
            r.append(json.loads(query)["query"])
            bar()

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


def get_page(
    article: tuple[str], redirects: dict, translations: dict, return_dict: dict
):
    global wikidump_de, wikidump_en
    key: str = article[1].removeprefix("/wiki/")
    redirect: str = redirects.get(key, key)
    nr = article[0]
    # try:
    page = {
        "de": xmltodict.parse(wikidump_de.get_page(redirect.replace("_", " ")))["page"],
        "en": xmltodict.parse(
            wikidump_en.get_page(
                translations.get(redirect.replace("_", " "), "23094739702347034")
            )
        )["page"],
    }

    api_call: dict = json.loads(
        requests.get(
            "https://de.wikipedia.org/api/rest_v1/page/summary/" + redirect,
            headers={"User-Agent": constants.USER_AGENT},
        ).text
    )

    return_dict["-".join(article)] = [
        page,
        api_call,
        key,
        redirect,
        nr,
    ]
    # except Exception as e:
    #     with open("articles.log", "a") as f:
    #         f.write(key + "\n" + str(e) + "\n\n\n")
    #         f.close()
    #     print("\033[91m", f"{key}", "\033[0m")


def scrape_articles(
    db=tuple[sqlite3.Cursor, sqlite3.Connection],
    mode: Literal["update", "refresh"] = "refresh",
) -> None:
    global wikidump_de, wikidump_en

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
    articles = [(nr, redirects.get(title, title)) for nr, title in articles]

    positions_de = pd.read_sql(
        f"SELECT * FROM pages WHERE title IN {tuple(set([title for nr, title in articles]))}",
        wikidump_de.index.conn,
    )
    positions_de.set_index("id", inplace=True)
    positions_de.sort_values("position")

    test = pd.read_sql(
        f"""SELECT t1.title, t1.position AS start, (SELECT MIN(t2.position) FROM pages t2 WHERE t1.title = t2.title AND t2.position > t1.position) AS stop
        FROM pages t1 WHERE t1.title IN {tuple(set([title for nr, title in articles]))}""",
        wikidump_de.index.conn,
    )

    print(test)

    return

    with alive_bar(
        len(positions_de.index), title=f"{mode.removesuffix('e')}ing articles"
    ) as bar:
        with open(constants.WIKIDUMP_DE, "rb") as f:
            for id, pos_title in positions_de.iterrows():
                pos, title = pos_title
                f.seek(pos)
                readback = f.read(end_byte - start_byte - 1)
                page_xml = BZ2Decompressor().decompress(readback).decode()
                f.close()
    return
    with alive_bar(len(articles), title=f"{mode.removesuffix('e')}ing articles") as bar:

        self.titles.set_index("id", inplace=True)
        self.titles.sort_values("position")
        _max = 10
        processes: list[Process] = [
            Process(
                target=get_page,
                args=(article, redirects, translations, return_dict),
                name="-".join(article),
            )
            for i, article in enumerate(articles[:_max])
        ]
        articles = articles[_max:]

        for process in processes:
            process.start()

        for process in processes:
            process.join()
            page, api_call, key, redirect, nr = return_dict[process.name]
            api_call: dict[str, dict]

            db[0].execute(
                f"INSERT INTO articles (key, title, title_en, id, episode, content, content_en, description, thumbnail) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    key,
                    page["de"]["title"],
                    translations.get(redirect.replace("_", " "), ""),
                    page["de"]["id"],
                    nr,
                    page["de"]["revision"]["text"]["#text"],
                    page["en"]["revision"]["text"].get("#text", ""),
                    api_call.get("extract", ""),
                    api_call.get("originalimage", {}).get("source", ""),
                ),
            )
            if len(articles):
                processes.append(
                    Process(
                        target=get_page,
                        args=(articles[0], redirects, translations, return_dict),
                        name="-".join(articles[0]),
                    )
                )
                processes[-1].start()
                articles.pop(0)
            bar()

            if len(articles) % 50 == 0:
                db[1].commit()


def refresh_articles(mode: Literal["update", "refresh"] = "refresh") -> pd.DataFrame:
    global wikidump_de, wikidump_en
    wikidump_de = Wikidump(constants.WIKIDUMP_DE, constants.WIKIDUMP_DE_INDEX)
    wikidump_en = Wikidump(constants.WIKIDUMP_EN, constants.WIKIDUMP_EN_INDEX)
    db = Database()

    if mode == "refresh":
        db.drop("articles")
    db.setup()

    scrape_articles((db.c, db.conn), mode=mode)

    db.close()
    wikidump_de.close()
    wikidump_en.close()
