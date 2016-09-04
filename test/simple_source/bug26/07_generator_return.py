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


# From 2.6 bsddb/__init.py
# Bug is return None in a generator inside
# an if.
def iteritems(self):
    if not self.db:
        return
    try:
        try:
            yield self.kv
        except:
            # the database was modified during iteration.  abort.
            pass
    except:
        self._in_iter -= 1
        raise
