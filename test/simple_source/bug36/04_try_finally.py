# From 3.6 _pyio.py
# Bug was in "return" not having "COME_FROM"
# and in 1st try/finally no END_FINALLY (which really
# hooks into the control-flow analysis).
# The 2nd try/finally has an END_FINALLY although still
# no "COME_FROM".

def getvalue(self):
    try:
        return 3
    finally:
        return 1


def getvalue1(self):
    try:
        return 4
    finally:
        pass
    return 2
