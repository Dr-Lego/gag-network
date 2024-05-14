from bz2 import BZ2File, BZ2Decompressor
from bs4 import BeautifulSoup
import constants
from typing import Iterable
from pathlib import Path
import pandas as pd
import xmltodict
import sqlite3
from alive_progress import alive_bar
from functools import lru_cache
import os


class Index(object):
    def __init__(self, path) -> None:
        self.path = Path(path)
        if not os.path.isfile(self.path):
            open(self.path, "w").close()

        self.conn: sqlite3.Connection = sqlite3.connect(
            self.path, check_same_thread=False
        )
        self.c: sqlite3.Cursor = self.conn.cursor()
        self.c.execute(
            "CREATE TABLE IF NOT EXISTS pages (position BIGINT, id INT, title VARCHAR(255))"
        )
        self.conn.commit()

    def add(self, position: int, id: int, title: str):
        self.c.execute(
            f"INSERT INTO pages (position, id, title) VALUES (?, ?, ?) ",
            [position, id, title],
        )

    def close(self):
        self.conn.commit()
        self.conn.close()


class Wikidump(object):
    def __init__(self, path: str, index_path: str) -> None:
        self.path = Path(path)
        self.index_path = index_path.replace(".bz2", ".sqlite")
        self.titles: pd.DataFrame = pd.DataFrame()

        if not os.path.isfile(self.index_path):
            self.index_to_db()
        else:
            self.index = Index(self.index_path)

    def index_to_db(self):
        print(
            "Please wait while an index database is being created to save memory and time in further operations. This can take some minutes."
        )
        self.index = Index(self.index_path)
        with BZ2File(Path(self.index_path.replace(".sqlite", ".bz2")), "r") as f:
            with alive_bar(unknown="waves") as bar:
                for l in f:
                    l = l.decode().removesuffix("\n")
                    if len(l):
                        l = l.split(":")
                        l = l[:2] + [":".join(l[2:])]
                        self.index.add(*l)
                    bar()

    def close(self):
        self.index.close()

    def set_titles(self, titles: Iterable):
        self.titles = pd.DataFrame(self.index.c.execute(
            f'SELECT * FROM pages WHERE title IN {tuple(titles)}'
        ).fetchall(), columns=["position", "id", "title"])
        self.titles.set_index("id", inplace=True)
        self.titles.sort_values("position")
        
    def get_pages(self):
        pass
        

    def get_byte_position(self, title: str) -> dict:
        data = self.index.c.execute(
            f'SELECT * FROM pages WHERE title LIKE "{title}"'
        ).fetchall()

        if not len(data):
            return {"data": data, "start": -1, "end": -1}

        data = next(iter([c for c in data if c[2] == title]), data[0])
        start_byte: int = data[0]
        end_byte = self.index.c.execute(
            f"SELECT MIN(position) FROM pages WHERE position > {start_byte}"
        ).fetchall()[0][0]
        return {"data": data, "start": start_byte, "end": end_byte}

    # @lru_cache(maxsize=None)
    def get_page(self, title: str) -> str:
        byte_position = self.get_byte_position(title)
        start_byte, end_byte = byte_position["start"], byte_position["end"]

        if start_byte == -1:
            return '<page><revision><text foo="bar"></text></revision></page>'

        with open(self.path, "rb") as f:
            f.seek(start_byte)
            readback = f.read(end_byte - start_byte - 1)
            page_xml = BZ2Decompressor().decompress(readback).decode()
            f.close()

        soup = BeautifulSoup(page_xml, "lxml")
        page_xml: str = [
            str(p) for p in soup.find_all("page") if p.find("title").text == title
        ][0]

        return page_xml


# de = Wikidump(constants.WIKIDUMP_DE, constants.WIKIDUMP_DE_INDEX)
# en = Wikidump(constants.WIKIDUMP_EN, constants.WIKIDUMP_EN_INDEX)

# en.set_titles(["United States", "Alboin", "Biometry", "Cunimund", "Rome", "Germany", "Pizza", "Sun", "Duck", "Book", "Martin Luther", "Paris", "ABC", "Telephone", "Cube", "Paper"])

# print(en.titles)


# # from multiprocessing import Pool, Process, Manager


# # def foo(title):
# #     en.get_page(title)
# #     print(title)

# # manager = Manager()
# # return_dict = manager.dict()#


# # _max = 5
# # fn = foo
# # args = ["United States", "Alboin", "Biometry", "Cunimund", "Rome", "Germany", "Pizza", "Sun", "Duck", "Book", "Martin Luther", "Paris", "ABC", "Telephone", "Cube", "Paper"]
# # processes: list[Process] = [Process(target=foo, args=(args[i],), name=args[i]) for i in range(_max)]
# # args = args[_max-1:]

# # for process in processes:
# #     process.start()

# # for process in processes:
# #     process.join()
# #     if len(args):
# #         processes.append(Process(target=foo, args=(args[0],), name=args[0]))
# #         processes[-1].start()
# #         args.pop(0)


# # xmltodict.parse(de.get_page("Alboin"))
# # xmltodict.parse(en.get_page("Alboin"))
# # print(1)
# # xmltodict.parse(de.get_page("Biometrie"))
# # xmltodict.parse(en.get_page("Biometrie"))
# # print(2)
# # xmltodict.parse(de.get_page("Kunimund"))
# # xmltodict.parse(en.get_page("Kunimund"))
# # print(3)
# de.close()
# en.close()
