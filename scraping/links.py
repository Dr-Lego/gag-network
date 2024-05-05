import wikitextparser as wtp
import pandas as pd
import sqlite3
from _Database import Database


def scrape_links(con:sqlite3.Connection):
    articles = pd.read_sql("SELECT * FROM articles", con=con)
    links: list[dict] = []


    for i, article in articles.iterrows():
        try:
            for a in wtp.parse(article["content"]).wikilinks:
                links.append({
                    "url": a.target,
                    "text": a.text if a.text else a.target,
                    "parent": article["title"],
                    "wikitext": str(a)
                })
            #print(f"{i+1}  {article['title']}")
        except:
            print("\033[91m", f"{i+1}  {article['title']}", "\033[0m")



    links = [dict(t) for t in {tuple(d.items()) for d in links}]
    df = pd.DataFrame(links)
    df.to_sql("links", con=con, if_exists="replace", index=False)
    return df


def refresh_links():
    db = Database()
    db.drop("links")
    db.setup()

    r = scrape_links(db.conn)

    db.close()

    return r