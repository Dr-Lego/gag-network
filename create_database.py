import sys
from scraping.episodes import refresh_episodes
from scraping.articles import refresh_articles
from scraping.links import refresh_links

"""
Refresh the database.
"""
    
if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0 or args == ["-u"]:
        refresh_episodes()
        refresh_articles("update" if "-u" in args else "refresh")
        refresh_links()
    else:
        options = ["--episodes", "--articles", "--links"]
        for option in options:
            if option in args:
                {"--episodes": refresh_episodes, "--articles": refresh_articles, "--links": refresh_links}[option]("update" if "-u" in args else "refresh")
