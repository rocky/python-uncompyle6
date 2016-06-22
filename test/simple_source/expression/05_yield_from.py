# Python 3.3 and above only
# Tests

# 3.3, 3.4
# yield_from ::= expr expr YIELD_FROM
# expr ::= yield_from

# 3.5:

def _walk_dir(dir, ddir=None):
    yield from _walk_dir(dir, ddir=dfile)
