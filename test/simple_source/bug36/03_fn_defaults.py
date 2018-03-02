# Python 3.6 changes, yet again, the way deafult pairs are handled
def foo1(bar, baz=1):
    return 1
def foo2(bar, baz, qux=1):
    return 2
def foo3(bar, baz=1, qux=2):
    return 3
def foo4(bar, baz, qux=1, quux=2):
    return 4

# From 3.6 compileall.
# Bug was in omitting default which when used in an "if"
# are treated as False would be
def _walk_dir(dir, ddir=None, maxlevels=10, quiet=0):
    return
