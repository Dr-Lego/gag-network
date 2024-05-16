import bz2
import pandas as pd
import ast
from typing import Iterable, Literal, IO
import itertools
from bs4 import BeautifulSoup
from multiprocessing import Process, Manager
import requests
import time
from bz2 import BZ2Decompressor
from werkzeug.datastructures import MultiDict
import sqlite3
from alive_progress import alive_bar
import json
import urllib.parse
import xmltodict
import numpy as np
import constants
from scraping._Wikidump import Wikidump
from scraping._Database import Database
from scraping._Index import Index


# wikidump_de: Wikidump = Wikidump(constants.WIKIDUMP_DE, constants.WIKIDUMP_DE_INDEX)
# wikidump_en: Wikidump = Wikidump(constants.WIKIDUMP_EN, constants.WIKIDUMP_EN_INDEX)
index_de: Index
index_en: Index


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
    global index_de, wikidump_en
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


def get_page(
    file: IO, title: str, start_byte: int, end_byte: int, return_dict, lang: str
):
    file.seek(start_byte)
    readback = file.read(end_byte - start_byte - 1)
    page_xml = BZ2Decompressor().decompress(readback).decode()
    soup = BeautifulSoup(page_xml, "lxml")
    page = soup.find("title", string=title).parent
    return_dict[lang] = xmltodict.parse(str(page))["page"]


def api_call(title: str, return_dict):
    return_dict["api"] = json.loads(
        requests.get(
            "https://de.wikipedia.org/api/rest_v1/page/summary/" + title,
            headers={"User-Agent": constants.USER_AGENT},
        ).text
    )


def scrape_articles(
    db=tuple[sqlite3.Cursor, sqlite3.Connection],
    mode: Literal["update", "refresh"] = "refresh",
) -> None:
    global index_de, index_en

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
    original_articles = {redirects.get(title, title): title for nr, title in articles}
    # titles mapped to episodes
    episodes_dict: MultiDict = MultiDict([(redirects.get(title, title), nr) for nr, title in articles])
    articles = [redirects.get(title, title) for nr, title in articles]

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
    for i in index.values():
        i.set_index("id", inplace=True)
        i.sort_values("start")

    wikidump_de: IO = open(constants.WIKIDUMP_DE, "rb")
    wikidump_en: IO = open(constants.WIKIDUMP_EN, "rb")
    
    with alive_bar(len(index["de"].index), title=f"refreshing articles") as bar:
        i = 0
        for id, row in index["de"].iterrows():
            row_en = index["en"].loc[
                index["en"].title == translations.get(row.title, "")
            ].iloc[0]

            manager = Manager()
            return_dict = manager.dict()

            # get german page, english page and summary/thumbnail in parallel
            processes = {
                "de": Process(
                    target=get_page,
                    args=(
                        wikidump_de,
                        row.title,
                        row.start,
                        row.end,
                        return_dict,
                        "de",
                    ),
                ),
                "en": Process(
                    target=get_page,
                    args=(
                        wikidump_en,
                        row_en.title,
                        row_en.start,
                        row_en.end,
                        return_dict,
                        "en",
                    )
                ) if not row_en.empty else None,
                "api": Process(target=api_call, args=(row.title, return_dict)),
            }

            for process in processes.values():
                if process:
                    process.start()
            for process in processes.values():
                if process:
                    process.join()
                
            page = return_dict
            
            data = ((
                    original_articles[row.title],
                    row.title,
                    row_en.title if not row_en.empty else "",
                    id),
                    (
                    page["de"]["revision"]["text"]["#text"],
                    page["en"]["revision"]["text"]["#text"] if "en" in page else "",
                    page["api"].get("extract", ""),
                    page["api"].get("originalimage", {}).get("source", ""))
            )

            db[0].executemany(
                f"INSERT INTO articles (key, title, title_en, id, episode, content, content_en, description, thumbnail) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ([*data[0], ep, *data[1]] for ep in episodes_dict.getlist(row.title))
            )
            
            if i % 50 == 0:
                db[1].commit()
            bar()
            if i == 5:
                break
            
    db[1].commit()

    wikidump_de.close()
    wikidump_en.close()

    return
    # with alive_bar(len(articles), title=f"{mode.removesuffix('e')}ing articles") as bar:

    #     self.titles.set_index("id", inplace=True)
    #     self.titles.sort_values("position")
    #     _max = 10
    #     processes: list[Process] = [
    #         Process(
    #             target=get_page,
    #             args=(article, redirects, translations, return_dict),
    #             name="-".join(article),
    #         )
    #         for i, article in enumerate(articles[:_max])
    #     ]
    #     articles = articles[_max:]

    #     for process in processes:
    #         process.start()

    #     for process in processes:
    #         process.join()
    #         page, api_call, key, redirect, nr = return_dict[process.name]
    #         api_call: dict[str, dict]

    #         db[0].execute(
    #             f"INSERT INTO articles (key, title, title_en, id, episode, content, content_en, description, thumbnail) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    #             (
    #                 key,
    #                 page["de"]["title"],
    #                 translations.get(redirect.replace("_", " "), ""),
    #                 page["de"]["id"],
    #                 nr,
    #                 page["de"]["revision"]["text"]["#text"],
    #                 page["en"]["revision"]["text"].get("#text", ""),
    #                 api_call.get("extract", ""),
    #                 api_call.get("originalimage", {}).get("source", ""),
    #             ),
    #         )
    #         if len(articles):
    #             processes.append(
    #                 Process(
    #                     target=get_page,
    #                     args=(articles[0], redirects, translations, return_dict),
    #                     name="-".join(articles[0]),
    #                 )
    #             )
    #             processes[-1].start()
    #             articles.pop(0)
    #         bar()

    #         if len(articles) % 50 == 0:
    #             db[1].commit()


def refresh_articles(mode: Literal["update", "refresh"] = "refresh") -> pd.DataFrame:
    global index_en, index_de
    # wikidump_de = Wikidump(constants.WIKIDUMP_DE, constants.WIKIDUMP_DE_INDEX)
    # wikidump_en = Wikidump(constants.WIKIDUMP_EN, constants.WIKIDUMP_EN_INDEX)
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
