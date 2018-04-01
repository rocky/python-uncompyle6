# Adapted from Python 3.3 idlelib/PyParse.py
# Bug is continue flowing back to while messing up the determination
# that it is inside an "if".

# RUNNABLE!
def _study1(i, n, ch):
    while i == 3:
        i = 4
        if ch:
            i = 10
            assert i < 5
            continue
        if n:
            return n

assert _study1(3, 4, False) == 4
