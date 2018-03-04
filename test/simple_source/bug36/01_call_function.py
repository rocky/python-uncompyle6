# Python 3.6's changes for calling functions.
# See https://github.com/rocky/python-uncompyle6/issues/58

# CALL_FUNCTION_EX takes 2 to 3 arguments on the stack:
# * the function,
# * the tuple of positional arguments, and optionally
# * the dict of keyword arguments if bit 0 of oparg is 1.
from foo import f, dialect, args, kwds, reader

f(*[])

# From Python 3.6 csv.py
# (f, dialect) are positional arg tuples, *args, is by itself, i.e.
# no tuple.
x = reader(f, dialect, *args, **kwds)

# From 3.6 functools.py
# Below there is a load_closure instruction added
def cmp_to_key(mycmp):
    class K(object):
        def __ge__():
            return mycmp()
    return

# In this situation though, there is no load_closure
def cmp2_to_key(mycmp):
    class K2(object):
        def __ge__():
            return 5
    return
