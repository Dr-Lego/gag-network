from scraping._Database import Database


db = Database()

db.c.execute(
  """
  SELECT distinct url FROM links WHERE url in (
      SELECT url FROM links
      WHERE url IN (SELECT title FROM articles)
      GROUP BY url having count(url) <= 5
  )
  """
)

# db.c.execute(
#   """
#   SELECT * FROM links
#   WHERE url LIKE "Kategorie:Geboren_1736"
#   """
# )


print("\n".join(["  ".join([str(x) for x in a]) for a in db.c.fetchall()]))

db.close()

