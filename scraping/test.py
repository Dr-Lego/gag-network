import wikitextparser as wtp
import colorama
from colorama import Back, Style


def context(text, links):
    refs = wtp.parse(text).get_tags("ref")
    for ref in refs:
        text = text.replace(str(ref), "")
    wikitext = wtp.parse(text)
    contexts = {}
    for s in wikitext.sections:
        results = [a for a in s.wikilinks if a.target in links]
        for link in results:
            text = s.plain_text().replace(link.plain_text(), f"[[{link.plain_text()}]]")
            text = "\n".join([l for l in text.split("\n") if not l.startswith("==") and not l.endswith("==")])
            contexts[link.target] = contexts.get(link.target, []) + [text]
    return contexts
        
        
text = open("scraping/article.md", "r").read()
print(context(text, ["Heinrich von Huntingdon",])) #"Heinrich von Huntingdon", 