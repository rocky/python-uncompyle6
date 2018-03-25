# From 2.7 test_argparse.py
# Bug was turning assert into an "or raise" statement
def __call__(arg, dest):
    try:
        assert arg == 'spam', 'dest: %s' % dest
    except:
        raise

__call__('spam', __file__)

# From python 2.7.14 lib2to3/refactor.py
# Bug was mangling assert turning if into "or"
def refactor_doctest(clipped, new):
    assert clipped, clipped
    if not new:
        new += u"\n"
    return

# From 2.7.14 test_hashlib.py
# The bug was turning assert into an "if"
# statement which isn't wrong, but we got the
# range of the if incorrect. When we have
# better control flow analysis we can revisit.
def test_threaded_hashing():
    for threadnum in xrange(1):
        result = 1
        assert result > 0
        result = 2
    return result

assert test_threaded_hashing() == 2
