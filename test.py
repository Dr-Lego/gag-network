import ast
import pandas as pd
import itertools
import numpy as np
import json
import requests
from alive_progress import alive_bar
from scraping._Database import Database

db = Database()
episodes = pd.read_sql("SELECT * FROM episodes", con=db.conn)
db.close()

episodes[["topics", "links"]] = episodes[["topics", "links"]].map(ast.literal_eval)

articles = list(zip(episodes["nr"], episodes["topics"]))
articles = [[(ep[0], a) for a in ep[1]] for ep in articles]
articles = list(itertools.chain.from_iterable(articles))


def in_english():
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
        
    return {"translations": translations, "redirects": redirects}
        
in_english()
