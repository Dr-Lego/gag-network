from bz2 import BZ2File
from pathlib import Path
import sqlite3
from alive_progress import alive_bar
import os

class Index(object):
    """
    A class to manage an index database for efficient data retrieval.
    """

    def __init__(self, index_path: str | Path) -> None:
        """
        Initialize the Index object.

        Args:
            index_path (str | Path): Path to the index file.
        """
        self.index_path = Path(index_path)
        self.path = Path(str(index_path).replace(".bz2", ".sqlite"))
        self.conn: sqlite3.Connection
        self.c: sqlite3.Cursor

        if not os.path.isfile(self.path):
            # Create a new SQLite database if it doesn't exist
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
        """
        Create the index database from a BZ2 compressed file.
        """
        print(
            "Please wait while an index database is being created to save memory and time in further operations. This can take some minutes."
        )

        with BZ2File(Path(str(self.index_path).replace(".sqlite", ".bz2")), "r") as f:
            with alive_bar(unknown="waves") as bar:
                cache = []
                pos = 0
                for l in f:
                    l = l.decode().removesuffix("\n")
                    if len(l):
                        l = l.split(":")
                        # Extract id, title, and start position
                        l = [l[1], ":".join(l[2:]), l[0]]
                        if l[2] != pos:
                            pos = l[2]
                            # Insert cached data into the database
                            self.c.executemany(
                                "INSERT INTO pages (id, title, start, end) VALUES (?, ?, ?, ?)",
                                (r + [pos] for r in cache),
                            )
                            cache = []
                        cache.append(l)
                    else:
                        print("end")
                        # Insert remaining cached data
                        self.c.executemany(
                            "INSERT INTO pages (id, title, start, end) VALUES (?, ?, ?, ?)",
                            (r + [pos] for r in cache),
                        )
                        cache = []
                    bar()

    def connect(self):
        """
        Establish a connection to the SQLite database.
        """
        self.conn: sqlite3.Connection = sqlite3.connect(
            self.path, check_same_thread=False
        )
        self.c: sqlite3.Cursor = self.conn.cursor()

    def add(self, position: int, id: int, title: str):
        """
        Add a new entry to the pages table.

        Args:
            position (int): The position of the entry.
            id (int): The ID of the entry.
            title (str): The title of the entry.
        """
        self.c.execute(
            f"INSERT INTO pages (position, id, title) VALUES (?, ?, ?) ",
            [position, id, title],
        )

    def close(self):
        """
        Commit changes and close the database connection.
        """
        self.conn.commit()
        self.conn.close()