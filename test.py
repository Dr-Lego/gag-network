from multiprocessing import Pool, Process, Manager

def foo(title):
    open("LICENSE.md", "r").read()
    print(title)

with Pool(5) as pool:
    pool.map(foo, ["Alboin", "Biometry", "Cunimund", "Rome", "Germany", "Pizza", "Sun", "Duck", "Book", "Martin Luther", "Paris", "ABC", "Telephone", "Cube", "Paper"])