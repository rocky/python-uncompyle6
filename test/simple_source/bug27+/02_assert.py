# From 2.7 test_argparse.py
# Bug was turnning assert into an "or raise" statement
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
