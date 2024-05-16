from bz2 import BZ2File, BZ2Decompressor
from bs4 import BeautifulSoup
from typing import Iterable
from pathlib import Path
import pandas as pd
import sqlite3
from alive_progress import alive_bar
import os
import constants


class Index(object):
    def __init__(self, index_path: str | Path) -> None:
        self.index_path = Path(index_path)
        self.path = Path(str(index_path).replace(".bz2", ".sqlite"))
        self.conn: sqlite3.Connection
        self.c: sqlite3.Cursor

        if not os.path.isfile(self.path):
            open(self.path, "w").close()
            self.connect()
            self.c.execute(
                "CREATE TABLE IF NOT EXISTS pages (id INT, title VARCHAR(255), start INT, end INT)"
            )
            self.conn.commit()
            self.create()
        else:
            self.connect()

    def create(self):
        print(
            "Please wait while an index database is being created to save memory and time in further operations. This can take some minutes."
        )

        with BZ2File(Path(str(self.index_path).replace(".sqlite", ".bz2")), "r") as f:
            with alive_bar(unknown="waves") as bar:
                cache = []  # pd.DataFrame(columns=["id", "title", "start"])
                pos = 0
                for l in f:
                    l = l.decode().removesuffix("\n")
                    if len(l):
                        l = l.split(":")
                        l = [l[1], ":".join(l[2:]), l[0]]
                        cache.append(l)
                        if l[2] != pos:
                            pos = l[2]
                            self.c.executemany(
                                "INSERT INTO pages (id, title, start, end) VALUES (?, ?, ?, ?)",
                                (r + [pos] for r in cache),
                            )
                            cache = []
                    else:
                        print("end")
                        self.c.executemany(
                            "INSERT INTO pages (id, title, start, end) VALUES (?, ?, ?, ?)",
                            (r + [pos] for r in cache),
                        )
                        cache = []
                    bar()

    def connect(self):
        self.conn: sqlite3.Connection = sqlite3.connect(
            self.path, check_same_thread=False
        )
        self.c: sqlite3.Cursor = self.conn.cursor()

    def add(self, position: int, id: int, title: str):
        self.c.execute(
            f"INSERT INTO pages (position, id, title) VALUES (?, ?, ?) ",
            [position, id, title],
        )

    def close(self):
        self.conn.commit()
        self.conn.close()


# import timeit
# import multiprocessing


# import xml.etree.ElementTree as ET
# import bz2


# i = Index(constants.WIKIDUMP_EN_INDEX)

# positions = pd.read_sql(
#     f"SELECT * FROM pages WHERE title LIKE 'Alexandria'",
#     i.conn,
# )
# print(positions)

# i.close()

# n = 0
# def get(pos):
#     start, end = pos
#     with open(constants.WIKIDUMP_EN, "rb") as f:
#         f.seek(start)
#         readback = f.read(end - start - 1)
#         page_xml = BZ2Decompressor().decompress(readback).decode()
#         f.close()
#     n+=1
#     print(n, end=" ")


# # 
# # with open("test.xml", "w") as f:
# #     f.write(get_wikitext(constants.WIKIDUMP_EN, 17584220))
# #     f.close()

# start_time = timeit.default_timer()

# with multiprocessing.Pool(10) as pool:
#     pool.map(get, [(17584220,18505627)]*1000)

# end_time = timeit.default_timer()
# print("Time taken:", end_time - start_time, "seconds")

# # print(n, end=" ")
