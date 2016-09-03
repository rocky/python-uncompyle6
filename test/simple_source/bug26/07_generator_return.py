# From python2.6/_abcoll.py
# Bug was producing "return None" which isn't
# allowed in a generator, instead of "return"
def __iter__(self):
    i = 0
    try:
        while True:
            v = self[i]
            yield v
            i += 1
    except IndexError:
        return
