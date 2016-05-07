# Python 3.3 and above only
# Tests

# yield_from ::= expr expr YIELD_FROM
# expr ::= yield_from

def _walk_dir(dir, ddir=None):
    yield from _walk_dir(dir, ddir=dfile)
