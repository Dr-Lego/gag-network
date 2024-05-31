import pandas as pd
import itertools
import requests
import json
import wikitextparser as wtp
from scraping._Database import Database

test = "test"
TEST = "test"

def scrape_episodes() -> pd.DataFrame:
    response = requests.get("https://de.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles=Geschichten_aus_der_Geschichte_(Podcast)/Episodenliste").text
    text = wtp.parse(list(json.loads(response)["query"]["pages"].values())[0]["revisions"][0]["*"])
    
    episodes = pd.DataFrame(itertools.chain.from_iterable([table.data() for table in text.tables]), columns=["nr", "date", "title", "subtitle", "topics", "duration", "links"])
    episodes = episodes.iloc[1:]
    episodes = episodes[episodes["date"] != "Datum"]
    episodes[["topics", "links"]] = episodes[["topics", "links"]].map(lambda cell: [str(a.target) if isinstance(a, wtp.WikiLink) else str(a.url) for a in wtp.parse(cell).wikilinks + wtp.parse(cell).external_links])
    episodes[["topics", "links"]] = episodes[["topics", "links"]].map(lambda cell: [a.strip().split("#")[0].replace("Heinrich_VIII._(England)", "Heinrich VIII. (England)") for a in cell])
    episodes["links"] = episodes["links"].map(lambda cell: [a for a in cell if not a.startswith("Datei:")])
    episodes[["topics", "links"]] = episodes[["topics", "links"]].map(lambda cell: json.dumps(cell, ensure_ascii=False))
    episodes.set_index("nr", inplace=True)
    episodes.rename(index=lambda i: f"GAG{i}" if len(i) <= 3 else i, inplace=True)
    
    return episodes


def refresh_episodes(*args) -> pd.DataFrame:
    db = Database()
    db.drop("episodes")
    db.setup()

    episodes_df = scrape_episodes()
    episodes_df.to_sql("episodes", con=db.conn, if_exists="replace")

    db.close()

    return episodes_df
