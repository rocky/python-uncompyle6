# From 3.7.3 dataclasses.py
# Bug was handling precedence. Need parenthesis before IfExp.
#
# RUNNABLE!
def _hash_add(fields):
    flds = [f for f in fields if (4 if f is None else f)]
    return flds

assert _hash_add([None, True, False, 3]) == [None, True, 3]
