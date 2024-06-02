import podcastparser
import urllib.request
from pprint import pprint

feedurl = 'https://geschichten-aus-der-geschichte.podigee.io/feed/mp3'
feed = podcastparser.parse(feedurl, urllib.request.urlopen(feedurl))
pprint({ep["link"].removesuffix("/").split("/")[-1]: ep.get("episode_art_url", feed["cover_url"]).split("=/")[-1] for ep in feed["episodes"]})