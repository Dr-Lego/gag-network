from bz2 import BZ2File, BZ2Decompressor
from bs4 import BeautifulSoup
import constants
from pathlib import Path
import sqlite3
from alive_progress import alive_bar
from functools import lru_cache
import os


class Index(object):
    def __init__(self, path) -> None:
        self.path = Path(path)
        if not os.path.isfile(self.path):
            open(self.path, "w").close()
        
        self.conn: sqlite3.Connection = sqlite3.connect(self.path)
        self.c: sqlite3.Cursor = self.conn.cursor()
        self.c.execute("CREATE TABLE IF NOT EXISTS pages (position BIGINT, id INT, title VARCHAR(255))")
        self.conn.commit()
        
    def add(self, position:int, id:int, title:str):
        self.c.execute(f"INSERT INTO pages (position, id, title) VALUES (?, ?, ?) ", [position, id, title])
    
    def close(self):
        self.conn.commit()
        self.conn.close()


class Wikidump(object):
    def __init__(self, path: str, index_path: str) -> None:
        self.path = path
        self.index_path = index_path.replace(".bz2", ".sqlite")
        # self.index: list = list(
        #     filter(None, BZ2File(index_path, "r").read().decode().split("\n"))
        # )
        if not os.path.isfile(self.index_path):
            self.index_to_db()
        else:
            self.index = Index(self.index_path)
            
        # self.byte_stops: list = list(
        #     sorted(set([int(i.split(":")[0]) for i in self.index]))
        # )
        self.decomp = BZ2Decompressor()
        
    def index_to_db(self):
        self.index = Index(self.index_path)
        with BZ2File(Path(self.index_path), "r") as f:
            with alive_bar(unknown="waves") as bar:
                for l in f:
                    if len(l):
                        l = l.split(":")
                        l = l[:2] + [":".join(l[2:])]
                        self.index.add(*l)
                    bar()
        
    def close(self):
        self.index.close()

    def get_index(self, title: str) -> tuple[int, str]:
        # find index of article in index file
        return next(
            iter(
                [
                    (i, row)
                    for i, row in enumerate(self.index)
                    if row.endswith(":" + title) and len(row.split(":")) == 3
                ]
            ),
            (-1, ""),
        )

    def get_byte_position(self, title: str) -> dict:
        i, data = self.get_index(title)
        start_byte: str = int(data.split(":")[0])
        end_byte = self.byte_stops[self.byte_stops.index(start_byte) + 1]
        return {"data": data, "start": start_byte, "end": end_byte}

    @lru_cache(maxsize=None)
    def get_page(self, title: str) -> str:
        byte_position = self.get_byte_position(title)
        start_byte, end_byte = byte_position["start"], byte_position["end"]
        
        with open(constants.WIKIDUMP_DE, "rb") as f:
            f.seek(start_byte)
            readback = f.read(end_byte - start_byte - 1)
            page_xml = self.decomp.decompress(readback).decode()
            f.close()
            
        soup = BeautifulSoup(page_xml, "lxml")
        page_xml: str = [
            str(p) for p in soup.find_all("page") if p.find("title").text == title
        ][0]
        
        return page_xml

wd = Wikidump(constants.WIKIDUMP_EN, constants.WIKIDUMP_EN_INDEX)
wd.close()