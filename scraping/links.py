import wikitextparser as wtp
import pandas as pd
import sqlite3
import json
from alive_progress import alive_bar
from scraping._Database import Database


def context(text) -> dict:
    refs = wtp.parse(text).get_tags("ref")
    for ref in refs:
        text = text.replace(str(ref), "")
    wikitext = wtp.parse(text)
    # if not len(links):
    #     links = [a.target for a in wikitext.wikilinks]
    contexts = {}
    for s in wikitext.sections:
        text = s.plain_text()
        #results = s.wikilinks#[a for a in s.wikilinks if a.target in links]
        for link in s.wikilinks:
            #.replace(link.plain_text(), f"[[{link.plain_text()}]]")
            #text = "\n".join([l for l in text.split("\n") if not l.startswith("==") and not l.endswith("==")])
            contexts[link.target] = contexts.get(link.target, []) + [text]
    return {"parsed": wikitext, "contexts": contexts}


def scrape_links(con:sqlite3.Connection):
    articles = pd.read_sql("SELECT * FROM articles", con=con)
    links: list[dict] = []

    with alive_bar(len(articles.index), title="refreshing links") as bar:
        for i, article in articles.iterrows():
            #try:
            #parsed, contexts = list(context(article["content"]).values())
            parsed = wtp.parse(article["content"])
            for a in parsed.wikilinks:
                links.append({
                    "url": a.target,
                    "text": a.text if a.text else a.target,
                    "parent": article["title"],
                    "wikitext": str(a),
                    #"context": json.dumps(contexts[a.target])
                })
            # except:
            #     print("\033[91m", f"{i+1}  {article['title']}", "\033[0m")
            bar()



    links = [dict(t) for t in {tuple(d.items()) for d in links}]
    df = pd.DataFrame(links)
    df.to_sql("links", con=con, if_exists="replace", index=False)
    return df


def refresh_links(*args):
    db = Database()
    db.drop("links")
    db.setup()

    r = scrape_links(db.conn)

    db.close()
    
    return r