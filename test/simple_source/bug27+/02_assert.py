# From 2.7 test_argparse.py
# Bug was turnning assert into an "or raise" statement
def __call__(arg, dest):
    try:
        assert arg == 'spam', 'dest: %s' % dest
    except:
        raise

__call__('spam', __file__)
