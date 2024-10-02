import os
import shutil
from datetime import datetime
import sqlite3
import constants

class Database(object):
    def __init__(self, path:str=constants.DATABASE) -> None:
        """
        Initializes the Database object.

        Args:
            path (str): Path to the SQLite database file. Defaults to constants.DATABASE.
        """
        self.path = path
        print(f"Connecting to database: {self.path}")
        self.conn: sqlite3.Connection = sqlite3.connect(self.path)
        self.c: sqlite3.Cursor = self.conn.cursor()
        
    def backup(self) -> None:
        """
        Creates a backup of the database file.
        """
        shutil.copy("data/articles.db", os.path.join("data/backup/", f"{datetime.now().strftime('%Y-%m-%d-%H_%M')}_articles_backup.db"))

    def drop(self, name:str=None):
        """
        Drops specified table(s) from the database.

        Args:
            name (str, optional): Name of the table to drop. If None, drops all tables.
        """
        if not name:
            for table in ["episodes", "articles", "links"]:
                self.c.execute(f"DROP TABLE IF EXISTS {table}")
        else:
            self.c.execute(f"DROP TABLE IF EXISTS {name}")
        self.conn.commit()

    def setup(self) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
        """
        Sets up the database by executing SQL commands from a file.

        Returns:
            tuple: A tuple containing the database connection and cursor.
        """
        self.c.executescript(open("scraping/create_tables.sql").read())
        self.conn.commit()
        return (self.conn, self.c)

    def close(self):
        """
        Commits changes and closes the database connection.
        """
        self.conn.commit()
        self.conn.close()