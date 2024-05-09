import wikitextparser as wtp
import colorama
from alive_progress import alive_bar
import time
import re
from colorama import Back, Style


# def context(text, links):
#     refs = wtp.parse(text).get_tags("ref")
#     for ref in refs:
#         text = text.replace(str(ref), "")
#     wikitext = wtp.parse(text)
#     contexts = {}
#     for s in wikitext.sections:
#         results = [a for a in s.wikilinks if a.target in links]
#         for link in results:
#             text = s.plain_text().replace(link.plain_text(), f"[[{link.plain_text()}]]")
#             text = "\n".join([l for l in text.split("\n") if not l.startswith("==") and not l.endswith("==")])
#             contexts[link.target] = contexts.get(link.target, []) + [text]
#     return contexts

# def mark_link(text, link):
#     wikitext = wtp.parse(text)
#     link = wtp.parse(link).wikilinks[0]
#     text = wikitext.plain_text(replace_wikilinks=False)
#     text = re.search(r"[^\]]{0,100}"+re.escape(link.string)+r"[^\[]{0,100}", text).group().replace(link.string, f"###{link.text if link.text else link.target}###")
#     return text
    
    
def compute():
    with alive_bar(10000) as bar:  # your expected total
        for item in range(0, 10000):        # the original loop
          bar()    
          time.sleep(0.01)# call `bar()` at the end


compute()
        
# text = "war ein [[bewaffneter Konflikt]], der von 1914 bis 1918 in [[Europa]], in [[Vorderasien]], in [[Afr"#open("scraping/article.md", "r").read()
# print(mark_link(text, "[[Europa]]"))