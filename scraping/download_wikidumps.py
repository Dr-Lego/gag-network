import requests
from bs4 import BeautifulSoup
import shutil
import bz2

def get_dump_url(url:str="https://dumps.wikimedia.org", lang:str="dewiki", offset=0):
    """
    Retrieve the URLs for the latest Wikipedia dump files.

    Args:
        url (str): Base URL for Wikimedia dumps.
        lang (str): Language code for the desired Wikipedia (e.g., "dewiki" for German).
        offset (int): Offset from the latest dump (0 for latest, 1 for previous, etc.).

    Returns:
        dict: URLs for the articles and index dump files.
    """
    # Get the directory page for the specified language
    dir_page = requests.get(url+"/"+lang).text
    soup = BeautifulSoup(dir_page, 'html.parser')
    
    # Find the desired dump date based on the offset
    log_page = list(sorted([int(node.get("href").replace("/","")) for node in soup.find_all("a") if node.get("href").startswith("2")]))[-offset-1]
    log_page: str = f'{url}/{lang}/{str(log_page)}'

    # Get the specific dump page
    log_page: str = requests.get(log_page).text
    soup = BeautifulSoup(log_page, 'html.parser')
    
    # Extract URLs for articles and index dumps
    dumps = [url + a["href"] for a in soup.find("li", {"class": "done"}).find_all("a")]
    return {"articles": dumps[0], "index": dumps[1]}

def download_index(url:str) -> str:
    """
    Download and decompress the index file.

    Args:
        url (str): URL of the index file.

    Returns:
        str: Decompressed content of the index file.
    """
    print("downloading index from", url)
    file = requests.get(url, stream=True).content
    print("saving...")
    with open("data/dump/index.txt.bz2", "wb") as f:
        f.write(file)
    print("decompressing...")
    decompressed = bz2.decompress(file)
    with open("data/dump/index.txt", "wb") as f:
        f.write(decompressed)
    return decompressed

def download_dump(url:str) -> str:
    """
    Download the articles dump file.

    Args:
        url (str): URL of the articles dump file.
    """
    print("downloading dump file from", url)
    download_file(url, "data/dump/articles.xml.bz2")

def download_file(url, path=None):
    """
    Download a file from a given URL.

    Args:
        url (str): URL of the file to download.
        path (str, optional): Local path to save the file. If None, uses the filename from the URL.

    Returns:
        str: Local filename of the downloaded file.
    """
    local_filename = url.split('/')[-1] if not path else path
    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    return local_filename

# Main execution
url = get_dump_url(offset=1)  # Get URLs for the previous dump (offset=1)
download_index(url["index"])  # Download and process the index file
download_dump(url["articles"])  # Download the articles dump file