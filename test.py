from multiprocessing import Pool
import functools

# -------------------------------------

def inc(x):
    return x + 1

def dec(x):
    return x - 1

def add(x, y):
    return x + y

# -------------------------------------

def smap(f):
    return f()

def main():
    f_inc = functools.partial(inc, 4)
    f_dec = functools.partial(dec, 2)
    f_add = functools.partial(add, 3, 4)
    with Pool() as pool:
        res = pool.map(smap, [f_inc, f_dec, f_add])
        print(res)

# -------------------------------------

if __name__ == '__main__':
    main()
