from bz2 import BZ2File
from pathlib import Path
import sqlite3
from alive_progress import alive_bar
import os


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
                        # id, title, start
                        l = [l[1], ":".join(l[2:]), l[0]]
                        if l[2] != pos:
                            pos = l[2]
                            self.c.executemany(
                                "INSERT INTO pages (id, title, start, end) VALUES (?, ?, ?, ?)",
                                (r + [pos] for r in cache),
                            )
                            cache = []
                        cache.append(l)
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
# import xmltodict


# # import xml.etree.ElementTree as ET
# # import bz2


# i = Index(constants.WIKIDUMP_DE_INDEX)

# TITLE = "Charles Lindbergh"

# pos = pd.read_sql(
#     f"SELECT * FROM pages WHERE title LIKE '{TITLE}'",
#     i.conn,
# ).iloc[0]
# print(pos)


# def get_page(path: str, title: str, start_byte: int, end_byte: int):
#     with open(path, "rb") as file:
#         file.seek(start_byte)
#         readback = file.read(end_byte - start_byte - 1)
#         file.close()
#     page_xml = BZ2Decompressor().decompress(readback).decode()
#     soup = BeautifulSoup(page_xml, "lxml")
#     page = soup.find("title", string=title).parent
#     print(title, path)
#     return xmltodict.parse(str(page))["page"]

# print(get_page(constants.WIKIDUMP_DE, TITLE, pos.start, pos.end))

# i.close()
