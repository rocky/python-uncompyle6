# From python 3.3.7 trace
# Bug was not having not having semantic rule for conditional not

# RUNNABLE!
def init(modules=None):
    mods = set() if not modules else set(modules)
    return mods

assert init() == set()
assert init([1, 2, 3]) == set([1, 2, 3])

# From 3.6 sre_parse
# Bug was in handling multple COME_FROMS from nested if's
def _escape(a, b, c, d, e):
    if a:
        if b:
            if c:
                if d:
                    raise
                return
        if e:
            if d:
                raise
            return
        raise

assert _escape(False, True, True,  True,  True) is None
assert _escape(True,  True, True,  False, True) is None
assert _escape(True,  True, False, False, True) is None

for args in (
        (True, True,  True, False, True),
        (True, False, True, True,  True),
        (True, False, True, True,  False),
        ):
    try:
        _escape(*args)
        assert False, args
    except:
        pass
