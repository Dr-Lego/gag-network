from bz2 import BZ2File, BZ2Decompressor
from bs4 import BeautifulSoup
import constants
from functools import lru_cache


class Wikidump(object):
    def __init__(self, path: str, index_path: str) -> None:
        self.path = path
        self.index: list = list(
            filter(None, BZ2File(index_path, "r").read().decode().split("\n"))
        )
        self.byte_stops: list = list(
            sorted(set([int(i.split(":")[0]) for i in self.index]))
        )
        self.decomp = BZ2Decompressor()

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
