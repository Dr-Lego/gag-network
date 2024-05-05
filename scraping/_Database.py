import os
import shutil
from datetime import datetime
import sqlite3


class Database(object):
    def __init__(self, path:str="data/gag.sqlite") -> None:
        self.path = path
        self.conn: sqlite3.Connection = sqlite3.connect(self.path)
        self.c: sqlite3.Cursor = self.conn.cursor()
        
    def backup(self) -> None:
        shutil.copy("data/articles.db", os.path.join("data/backup/", f"{datetime.now().strftime('%Y-%m-%d-%H_%M')}_articles_backup.db"))

    def drop(self, name:str=None):
        if not name:
            for table in ["episodes", "articles", "links"]:
                self.c.execute(f"DROP TABLE IF EXISTS {table}")
        else:
            self.c.execute(f"DROP TABLE IF EXISTS {name}")
        self.conn.commit()

    def setup(self) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
        self.c.executescript(open("scraping/create_tables.sql").read())
        # self.c.execute("CREATE TABLE IF NOT EXISTS episodes (nr VARCHAR(10), date DATE, title VARCHAR(255), subtitle TEXT,  topics TEXT, duration VARCHAR(5), links VARCHAR(120))")
        # self.c.execute("CREATE TABLE IF NOT EXISTS articles (key VARCHAR(100), title VARCHAR(100), id INTEGER, episode VARCHAR(20), content TEXT)")
        # self.c.execute("CREATE TABLE IF NOT EXISTS links (url VARCHAR(100), text VARCHAR(255), parent VARCHAR(100), wikitext VARCHAR(255))")
        self.conn.commit()
        return (self.conn, self.c)

    def insert_article(self, key:str, title: str, id:int, content: str):
        keys, values = list(locals().keys())[1:], list(locals().values())[1:]
        self.c.execute(f"INSERT INTO articles ({','.join(keys)}) VALUES ({','.join(len(keys)*'?')})", values)
        self.conn.commit()

    def close(self):
        self.conn.commit()
        self.conn.close()
