# From 3.6 _collections.abc.py
# Bug was try/execpt parsing detection since 3.6 removes
# a JUMP_FORWARD from earlier 3.xs.
# This could also get confused with try/else.

# RUNNABLE!
def iter(self):
    i = 0
    try:
        while True:
            v = self[i]
            yield v
            i += 1
    except IndexError:
        return


A = [10, 20, 30]
assert list(iter(A)) == A
