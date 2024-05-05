from typing import Literal, Iterable
import itertools
import ast
import json
import time
import requests
import pandas as pd
from _Database import Database


def scrape_articles(db=Iterable, mode:Literal["update","refresh"]="update") -> None:
    episodes = pd.read_sql("SELECT * FROM episodes", con=db[1])
    episodes[["topics", "links"]] = episodes[["topics", "links"]].map(ast.literal_eval)

    articles = list(zip(episodes["nr"], episodes["topics"]))
    articles = [[(ep[0], a) for a in ep[1]] for ep in articles]
    articles = list(itertools.chain.from_iterable(articles))
    #articles = list(sorted(set([t.removeprefix("/wiki/") for t in articles if t.startswith("/wiki/")])))

    if mode == "update":
        articles = list(sorted(set(articles) - set(pd.read_sql("SELECT * FROM articles", con=db[1])["key"].to_list())))


    for i, episode in enumerate(articles):
        topic = episode[1].removeprefix("/wiki/")
        nr = episode[0]
        try:
            r = json.loads(requests.get(
                "https://api.wikimedia.org/core/v1/wikipedia/de/page/" + topic,
                headers= {
                    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJjYzZmOGE2MmVkYWE0NmM1NGY0ZjZkNjVjNzIyZmZhZiIsImp0aSI6IjJjYzE4NjE0NzAxZDBhYWRjZDAwYmEyMGUxZTdkZTYwNjI0OTM1MmIzNjhiNjZmZjFlMTNkZTlhZGE3MzI1ZTdmMjFhNWExZDZkOTUwNjQ4IiwiaWF0IjoxNzEzNzA2MjU2LjgxNTQ3LCJuYmYiOjE3MTM3MDYyNTYuODE1NDc0LCJleHAiOjMzMjcwNjE1MDU2LjgxMzk0Niwic3ViIjoiNzU0Nzk5ODkiLCJpc3MiOiJodHRwczovL21ldGEud2lraW1lZGlhLm9yZyIsInJhdGVsaW1pdCI6eyJyZXF1ZXN0c19wZXJfdW5pdCI6NTAwMCwidW5pdCI6IkhPVVIifSwic2NvcGVzIjpbImJhc2ljIl19.Ig8lvCrcqivVJMju7794yq3HrTtI3ocVTGAXB71XZZYnd9SmZeHGjuTKWSh9uF2cJgG_jIoSVNa3HAYBY2XAJrwR6FQnHuqsQ6xrKs5VBGVc0Lopsjv0rck-g81F8nCu5aNqPgCmeU0uLFxqlYT58k_64PBehOvpSeu8O605tmx5WTf4u2AinCMfeHXI2aSv7h-f7PwDDvmaQrOMSVp04Ty0OuY5mDoQPA-LT29lBcRMC79-uGe03YEtHjFbqfGM1ALOATc7VTWA2-XoV47ZulwvE0OJZGphbAUnE6zoYBLpXNH_LALRyhB9yukm4kcW4rWvGzhgAQrCHesAEK7ZDdhi1C7EF6Q_oyH_I_Zx0r-LbkXGanq47Uu1ErQWNMd2IN45bCKIg887FYAOhSwJtgEuVEKuyskW2RZN3-psz2gXlbz35CgZ68paogGW8kj6Yu0L-sz-_P8GGeNyYu4ncvOcckDjUowR7jbli77aj6Yjr3nZabAXtIzShOTIZ-uA85JzRtYhkT29j5goYvN2gYZGLvTIYqT8vykoUT4r4H08QCLIFQCbA0jXSCuN0RqgQfUj6uwtAoMXe3T7NKAkW12ghNqUmsjYwfm_XTMwUxf5s9PeultFPWdYX3qTJ_lZ8iZ2VCXvGdWaMBEwXVT3_LWR6dRzMLrek2qTFRX2bhU',
                    'User-Agent': 'GAG-Mining (Dr_Lego@ist-einmalig.de)'
                }
            ).text)
            key = r["key"]
            if "redirect_target" in r:
                r = json.loads(requests.get("https://de.wikipedia.org/" + r["redirect_target"]).text)
            db[0].execute(f"INSERT INTO articles (key, title, id, episode, content) VALUES (?, ?, ?, ?, ?)", (key, r["title"], r["id"], nr, r["source"]))
            if i%50 == 0:
                db[1].commit()
            print(f"{i+1}/{len(articles)}     {topic}   {nr}")
            time.sleep(0.5)
        except Exception as e:
            with open("log.log", "a") as f:
                f.write(topic+"\n"+str(e)+"\n\n\n")
                f.close()
            print("\033[91m", f"{i+1}/{len(articles)}     {topic}", "\033[0m")



def refresh_articles(mode:Literal["update","refresh"]="update") -> pd.DataFrame:
    db = Database()
    if mode == "refresh":
        db.drop("articles")
    db.setup()

    scrape_articles((db.c, db.conn), mode=mode)

    db.close()