# Issue #413 on 2.7
# Bug in handling CONTINUE in else block of if-then-else in a for loop

"""This program is self-checking!"""
def test1(a, r = None):
    for b in a:
        if b:
            r = b
        else:
            continue
            raise AssertionError("CONTINUE not followed")
        if b:
            pass
    return r

def test2(a, r = None):
    for b in a:
        if b:
            #pass # No payload
            continue
            raise AssertionError("CONTINUE not followed")
        else:
            continue
            raise AssertionError("CONTINUE not followed")
        if b:
            r = b
        raise AssertionError("CONTINUE not followed")
    return r

assert test1([True]) == True, "Incorrect flow"
assert test2([True]) is None, "Incorrect flow"
assert test1([False]) is None, "Incorrect flow"
assert test2([False]) is None, "Incorrect flow"
