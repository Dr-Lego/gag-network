from episodes import refresh_episodes
from articles2 import refresh_articles
from links import refresh_links

def cprint(text:str):
    print("\033[1m\033[95m"+text+"\033[0m")

# refresh_episodes()
# cprint("episodes refreshed")

# refresh_articles("refresh")
# cprint("articles refreshed")

refresh_links()
cprint("links refreshed")