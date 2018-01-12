# From idlelib/PyParse.py
# Bug is "if" inside a nested while/else.
def _study1(i, n):
    while i:
        while i:
            i = 0
        else:
            if i:
                i = 1
