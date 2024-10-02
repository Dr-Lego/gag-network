CREATE TABLE IF NOT EXISTS episodes (
    nr VARCHAR(10),
    date DATE,
    title VARCHAR(255),
    subtitle TEXT,
    topics TEXT,
    duration VARCHAR(5),
    links VARCHAR(120)
);
CREATE TABLE IF NOT EXISTS articles (
    key VARCHAR(100),
    title VARCHAR(100),
    title_en VARCHAR(100),
    id INTEGER,
    episode VARCHAR(20),
    content TEXT,
    content_en TEXT,
    description TEXT,
    thumbnail VARCHAR(250)
);
CREATE TABLE IF NOT EXISTS links (
    url VARCHAR(100),
    text VARCHAR(255),
    parent VARCHAR(100),
    wikitext VARCHAR(255)
)