# From python 3.3.7 trace
# Bug was not having not having semantic rule for conditional not

# RUNNABLE!
def init(modules=None):
    mods = set() if not modules else set(modules)
    return mods

assert init() == set()
assert init([1, 2, 3]) == set([1, 2, 3])
