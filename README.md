![](https://github.com/[username]/[reponame]/blob/[branch]/image.jpg?raw=true)

# `Geschichten aus der Geschichte` Network Visualizer

This project aims to visualize the intricate web of connections within the German podcast ["Geschichten aus der Geschichte"](https://www.geschichte.fm) (Stories from History). It creates a network visualization based on the podcast's [episode list on Wikipedia](https://de.wikipedia.org/w/index.php?title=Geschichten_aus_der_Geschichte_(Podcast)/Episodenliste&useskin=vector), showcasing how the Wikipedia articles of the topics mentioned in the podcast are interconnected.

## Project Overview

The GAG Network Visualizer scrapes data from Wikipedia, processes it, and generates a interactive network graph. It reveals interesting connections between historical topics discussed in the podcast episodes.

Key features:
- Scrapes podcast episode data and related Wikipedia articles
- Processes and analyzes links between articles
- Generates a visual network of interconnected topics
- Provides an interactive web interface to explore the network

## Technical Details

The project is primarily written in Python and uses various libraries for web scraping, data processing, and visualization. It includes:

- Web scraping using `requests`, `BeautifulSoup`, and `Selenium`
- Data processing with `pandas` and `numpy`
- Text parsing with `wikitextparser`
- Multiprocessing for improved performance
- SQLite database for data storage
- JavaScript-based network visualization, using `vis.js`

### Performance Optimization

Significant effort has been put into optimizing the performance of this project as processing complete Wikipedia dumps:
- Wikipedia index file is converted to an sqlite database at the beginning to make it searchable more easily.
- Utilizes multiprocessing for parallel execution of tasks.
- Uses database indexing and optimized SQL queries to speed up data retrieval.
- Pre-loads and compresses network data to reduce initial loading times for the visualization.

# Prerequisites
- Chrome browser (for Selenium WebDriver, you can optionally change the used browser in the `build.py`file)
- install required python libraries using `pip install -r requirements.txt`
## Downloading Wikipedia Dumps

Open [dumps.wikimedia.org/dewiki](https://dumps.wikimedia.org/dewiki/) and [dumps.wikimedia.org/enwiki](https://dumps.wikimedia.org/enwiki/), respectively, and open the directory with the latest timestamp. If the dump is completed, download the two topmost files, called `*-pages-articles-multistream.xml.bz2`and `*-pages-articles-multistream-index.txt.bz2`

## Setting Up Environment Variables

You need to set several environment variables that define the user agent, database path, and paths to the Wikipedia dump files.

```bash
GAG_USER_AGENT="GAG-Network (your-email@example.com)"
GAG_DATABASE="/path/to/database"
GAG_WIKIDUMP_DE="/path/to/german/wikipedia-dump.xml.bz2"
GAG_WIKIDUMP_DE_INDEX="/path/to/german/wikipedia-dump-index.txt.bz2" 
GAG_WIKIDUMP_EN="/path/to/english/wikipedia-dump.xml.bz2"
GAG_WIKIDUMP_EN_INDEX="/path/to/english/wikipedia-dump-index.txt.bz2" 
```


# Running the project


To update the connections database and create a new static build of the network, run `main.py`. 

## Project Workflow
- The script first scrapes episode data and related Wikipedia articles. (`scraping/episodes.py`)
- It then processes the data, extracting links and creating a network structure. (`scraping/articles.py`, `scraping/links.py`)
- The network data is saved in JavaScript files for visualization and preloaded network is created using Selenium WebDriver for faster initial loading. (`build.py`)