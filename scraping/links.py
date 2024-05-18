import wikitextparser as wtp
import pandas as pd
import sqlite3
from alive_progress import alive_bar
from scraping._Database import Database


def scrape_links(con: sqlite3.Connection):
    articles = pd.read_sql(
        "SELECT DISTINCT key, title, title_en, id, content, content_en, description, thumbnail FROM articles",
        con=con,
    )
    translations = {
        en: de[0]
        for en, de in pd.read_sql(
            "SELECT DISTINCT title, title_en FROM articles", con=con
        )
        .set_index("title_en")
        .T.to_dict("list")
        .items()
    }
    links: list[dict] = []

    with alive_bar(len(articles.index), title="refreshing links") as bar:
        for i, article in articles.iterrows():
            parsed = wtp.parse(article["content"])
            for a in parsed.wikilinks:
                links.append(
                    {
                        "url": a.target,
                        "text": a.text if a.text else a.target,
                        "parent": article["title"],
                        "wikitext": str(a),
                        "lang": "de",
                    }
                )
            if article["content_en"]:
                parsed = wtp.parse(article["content_en"])
                for a in parsed.wikilinks:
                    links.append(
                        {
                            "url": translations.get(a.target, a.target),
                            "text": a.text if a.text else a.target,
                            "parent": article["title"],
                            "wikitext": str(a),
                            "lang": "en",
                        }
                    )

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
