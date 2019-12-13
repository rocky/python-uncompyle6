# from 3.7 inspect.py
# Bug was "if not predicate or" inside "for".
# Jump optimization turns a POP_JUMP_IF_TRUE into
# a POP_JUMP_IF_FALSE and this has to be
# dealt with at the "if" (or actually "testfalse") level.

# RUNNABLE!
def getmembers(names, object, predicate):
    for key in names:
        if not predicate or object:
            object = 2
        object += 1
    return object

assert getmembers([1], 0, False) == 3
assert getmembers([1], 1, True) == 3
assert getmembers([1], 0, True) == 1
assert getmembers([1], 1, False) == 3
assert getmembers([], 1, False) == 1
assert getmembers([], 2, True) == 2

def _shadowed_dict(klass, a, b, c):
    for entry in klass:
        if not (a and b):
            c = 1
    return c

assert _shadowed_dict([1], True, True, 3) == 3
assert _shadowed_dict([1], True, False, 3) == 1
assert _shadowed_dict([1], False, True, 3) == 1
assert _shadowed_dict([1], False, False, 3) == 1
assert _shadowed_dict([], False, False, 3) == 3

# Bug: the double "and" comes out as if .. if not and
def _shadowed_dict2(klass, a, b, c, d):
    for entry in klass:
        if not (a and b and c):
            d = 1
    return d

# Not yet --
# assert _shadowed_dict2([1], False, False, False, 3) == 1
# assert _shadowed_dict2([1], True, True, True, 3) == 3
