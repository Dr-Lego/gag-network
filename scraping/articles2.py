import bz2
import pandas as pd
import ast
from _Database import Database
from typing import Iterable, Literal
import itertools
import threading
import wikitextparser as wtp
import requests
import time
import numpy as np
import json
import xmltodict
from bs4 import BeautifulSoup
import string


def get_index() -> str:
    return open("data/dump/index.txt", "r").read()


def get_episode(title: str, index: str) -> tuple:
    for i, row in enumerate(index):
        if row.endswith(":" + title) and len(row.split(":")) == 3:
            return (i, row)
    return (-1, "")


def get_byte_position(title: str) -> dict:
    global byte_positions, index
    _, data = get_episode(title, index)
    start_byte = data.split(":")[0]
    end_byte = int(
        next(
            iter(
                [
                    row.split(":")[0]
                    for row in index[_ : _ + 110]
                    if row.split(":")[0] != start_byte
                ]
            )
        )
    )
    start_byte = int(start_byte)
    byte_positions[title] = {"data": data, "start": start_byte, "end": end_byte}
    return {"data": data, "start": start_byte, "end": end_byte}


def get_page_xml(title: str) -> str:
    global byte_positions
    decomp = bz2.BZ2Decompressor()
    byte_position = get_byte_position(title) #byte_positions[title]#
    start_byte, end_byte = byte_position["start"], byte_position["end"]
    with open("data/dump/articles.xml.bz2", "rb") as f:
        f.seek(start_byte)
        readback = f.read(end_byte - start_byte - 1)
        page_xml = decomp.decompress(readback).decode()
        f.close()

    soup = BeautifulSoup(page_xml, "lxml")
    with open("test.xml", "w") as f:
        f.write(page_xml)
        f.close()
    try:
        page_xml: str = [
            str(p) for p in soup.find_all("page") if p.find("title").text == title
        ][0]
    except:
       print(byte_position)
    return page_xml



def get_byte_positions(articles):
    threads = []
    for i in range(len(articles)):
        t = threading.Thread(target=get_byte_position, args=(articles[i],))
        t.start()
        threads.append(t)

    for thread in threads:
        thread.join()
        

index: str = get_index().split("\n")
byte_positions: dict = {}


def scrape_articles(db=Iterable, mode: Literal["update", "refresh"] = "update") -> None:
    episodes = pd.read_sql("SELECT * FROM episodes", con=db[1])
    episodes[["topics", "links"]] = episodes[["topics", "links"]].map(ast.literal_eval)

    articles = list(zip(episodes["nr"], episodes["topics"]))
    articles = [[(ep[0], a) for a in ep[1]] for ep in articles]
    articles = list(itertools.chain.from_iterable(articles))

    
    if mode == "update":
        _keys = ["/wiki/"+k for k in pd.read_sql("SELECT * FROM articles", con=db[1])["key"].to_list()]
        articles = list([a for a in articles if a[1] not in _keys])
        

    for i, episode in enumerate(articles):
        key = episode[1].removeprefix("/wiki/")#
        nr = episode[0]
        try:
            page = {"title": ""}
            page: dict = xmltodict.parse(get_page_xml(key.replace("_", " ")))["page"]
            if page.get("redirect", False):
                page: dict = xmltodict.parse(get_page_xml(page["redirect"]["@title"]))["page"]
            page["text"] = page["revision"]["text"]["#text"]
            
            api_call: dict = json.loads(requests.get(
                "https://de.wikipedia.org/api/rest_v1/page/summary/" + key,
                headers= {
                    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJjYzZmOGE2MmVkYWE0NmM1NGY0ZjZkNjVjNzIyZmZhZiIsImp0aSI6IjJjYzE4NjE0NzAxZDBhYWRjZDAwYmEyMGUxZTdkZTYwNjI0OTM1MmIzNjhiNjZmZjFlMTNkZTlhZGE3MzI1ZTdmMjFhNWExZDZkOTUwNjQ4IiwiaWF0IjoxNzEzNzA2MjU2LjgxNTQ3LCJuYmYiOjE3MTM3MDYyNTYuODE1NDc0LCJleHAiOjMzMjcwNjE1MDU2LjgxMzk0Niwic3ViIjoiNzU0Nzk5ODkiLCJpc3MiOiJodHRwczovL21ldGEud2lraW1lZGlhLm9yZyIsInJhdGVsaW1pdCI6eyJyZXF1ZXN0c19wZXJfdW5pdCI6NTAwMCwidW5pdCI6IkhPVVIifSwic2NvcGVzIjpbImJhc2ljIl19.Ig8lvCrcqivVJMju7794yq3HrTtI3ocVTGAXB71XZZYnd9SmZeHGjuTKWSh9uF2cJgG_jIoSVNa3HAYBY2XAJrwR6FQnHuqsQ6xrKs5VBGVc0Lopsjv0rck-g81F8nCu5aNqPgCmeU0uLFxqlYT58k_64PBehOvpSeu8O605tmx5WTf4u2AinCMfeHXI2aSv7h-f7PwDDvmaQrOMSVp04Ty0OuY5mDoQPA-LT29lBcRMC79-uGe03YEtHjFbqfGM1ALOATc7VTWA2-XoV47ZulwvE0OJZGphbAUnE6zoYBLpXNH_LALRyhB9yukm4kcW4rWvGzhgAQrCHesAEK7ZDdhi1C7EF6Q_oyH_I_Zx0r-LbkXGanq47Uu1ErQWNMd2IN45bCKIg887FYAOhSwJtgEuVEKuyskW2RZN3-psz2gXlbz35CgZ68paogGW8kj6Yu0L-sz-_P8GGeNyYu4ncvOcckDjUowR7jbli77aj6Yjr3nZabAXtIzShOTIZ-uA85JzRtYhkT29j5goYvN2gYZGLvTIYqT8vykoUT4r4H08QCLIFQCbA0jXSCuN0RqgQfUj6uwtAoMXe3T7NKAkW12ghNqUmsjYwfm_XTMwUxf5s9PeultFPWdYX3qTJ_lZ8iZ2VCXvGdWaMBEwXVT3_LWR6dRzMLrek2qTFRX2bhU',
                    'User-Agent': 'GAG-Mining (Dr_Lego@ist-einmalig.de)'
                }
            ).text)
            description, thumbnail = api_call.get("extract", ""), api_call.get("originalimage", {}).get("source", "")
            
            db[0].execute(f"INSERT INTO articles (key, title, id, episode, content, description, thumbnail) VALUES (?, ?, ?, ?, ?, ?, ?)", (key, page["title"], page["id"], nr, page["text"], description, thumbnail))
            
            if i%50 == 0:
                db[1].commit()
            print(f"{i+1}/{len(articles)}     {key}   {nr}")
            time.sleep(0.5)
        except Exception as e:
            with open("log.log", "a") as f:
                f.write(page["title"] + "\n" + str(e) + "\n\n\n")
                f.close()
            print("\033[91m", f"{i+1}/{len(articles)}     {key}", "\033[0m")


def refresh_articles(mode: Literal["update", "refresh"] = "update") -> pd.DataFrame:
    db = Database()
    if mode == "refresh":
        db.drop("articles")
    db.setup()

    scrape_articles((db.c, db.conn), mode=mode)

    db.close()
    
    
# refresh_articles("refresh")

