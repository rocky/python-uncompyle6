# From python3.8/distutils/version.py with optimization -O2
# The bug was that the other "else" constant propagated removed.

# NOTE: this program needs to be compile with optimization
def _cmp (b, c):
    if b:
        if c:
            return 0
        else:
            return 1
    else:
        assert False, "never get here"
