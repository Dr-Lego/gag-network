import wikitextparser as wtp
import pandas as pd
import sqlite3
from alive_progress import alive_bar
from scraping._Database import Database

def scrape_links(con: sqlite3.Connection) -> pd.DataFrame:
    """
    Scrape links from article content and store them in the database.

    Args:
        con (sqlite3.Connection): Database connection object.

    Returns:
        pd.DataFrame: DataFrame containing the scraped links.
    """
    # Fetch articles from the database
    articles = pd.read_sql(
        "SELECT DISTINCT key, title, title_en, id, content, content_en, description, thumbnail FROM articles",
        con=con,
    )

    # Create a translation dictionary for English to German titles
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

    # Process each article and extract links
    with alive_bar(len(articles.index), title="refreshing links") as bar:
        for i, article in articles.iterrows():
            # Process German content
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
            
            # Process English content if available
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

    # Remove duplicates and convert to DataFrame
    links = [dict(t) for t in {tuple(d.items()) for d in links}]
    df = pd.DataFrame(links)

    # Save links to the database
    df.to_sql("links", con=con, if_exists="replace", index=False)
    return df

def refresh_links(*args) -> pd.DataFrame:
    """
    Refresh the links table in the database.

    Args:
        *args: Variable length argument list (not used in the function).

    Returns:
        pd.DataFrame: DataFrame containing the refreshed links.
    """
    db = Database()
    db.drop("links")  # Drop existing links table
    db.setup()  # Set up new table structure

    r = scrape_links(db.conn)  # Scrape new link data

    db.close()

    return r
