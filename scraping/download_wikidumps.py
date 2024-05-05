import requests
from bs4 import BeautifulSoup
import shutil
import bz2

def get_dump_url(url:str="https://dumps.wikimedia.org", lang:str="dewiki", offset=0):
    dir_page = requests.get(url+"/"+lang).text
    soup = BeautifulSoup(dir_page, 'html.parser')
    log_page = list(sorted([int(node.get("href").replace("/","")) for node in soup.find_all("a") if node.get("href").startswith("2")]))[-offset-1]
    log_page: str = f'{url}/{lang}/{str(log_page)}'

    log_page: str = requests.get(log_page).text
    soup = BeautifulSoup(log_page, 'html.parser')
    dumps = [url + a["href"] for a in soup.find("li", {"class": "done"}).find_all("a")]
    return {"articles": dumps[0], "index": dumps[1]}


def download_index(url:str) -> str:
    print("downloading index from", url)
    file = requests.get(url, stream=True).content
    print("saving...")
    with open("data/dump/index.txt.bz2", "wb") as f:
        f.write(file)
        f.close()
    print("decompressing...")
    decompressed = bz2.decompress(file)
    with open("data/dump/index.txt", "wb") as f:
        f.write(decompressed)
        f.close()

    return decompressed


def download_dump(url:str) -> str:
    print("downloading dump file from", url)
    download_file(url, "data/dump/articles.xml.bz2")


def download_file(url, path=None):
    local_filename = url.split('/')[-1] if not path else path
    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename



url = get_dump_url(offset=1)
download_index(url["index"])
download_dump(url["articles"])

