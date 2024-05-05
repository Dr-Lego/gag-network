from urllib.parse import unquote_plus
import pandas as pd
from bs4 import BeautifulSoup
import requests
from _Database import Database


def scrape_episodes() -> pd.DataFrame:
    """
    Scrape episode data from the Wikipedia page for the "Geschichten aus der Geschichte" podcast.

    Returns:
        pd.DataFrame: A DataFrame containing data for each episode.
    """
    response = requests.get("https://de.wikipedia.org/wiki/Geschichten_aus_der_Geschichte_(Podcast)/Episodenliste")
    response.encoding = "UTF-8"
    soup = BeautifulSoup(response.text, "lxml")

    episodes: list[dict] = []

    for year_table in soup.find_all(class_="wikitable"):
        for episode_row in year_table.select("tbody > tr"):
            data = [
                str(cell.text).strip()
                if i not in [4, 6]
                else list([unquote_plus(a["href"]) for a in cell.find_all("a", href=True) if (not ("#" in a["href"] or a["href"].startswith("/w/")) ) and not "Dungeons" in a["href"]])
                for i, cell in enumerate(episode_row.find_all("td"))
            ]
            episode = dict(zip(["nr", "date", "title", "subtitle", "topics", "duration", "links"], [str(x) for x in data]))
            if episode:
                episodes.append(episode)

    df = pd.DataFrame(episodes)
    df.set_index("nr", inplace=True)
    df.rename(index=lambda i: f"GAG{i}" if len(i) <= 3 else i, inplace=True)
    return df



def refresh_episodes() -> pd.DataFrame:
    db = Database()
    db.drop("episodes")
    db.setup()

    episodes_df = scrape_episodes()
    episodes_df.to_sql("episodes", con=db.conn, if_exists="replace")

    db.close()

    return episodes_df
