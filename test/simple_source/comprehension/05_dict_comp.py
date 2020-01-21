# Bug was in dictionary comprehension involving "if not"
# Issue #162
#
# This code is RUNNABLE!
def x(s):
    return {k: v for (k, v) in s if not k.startswith("_")}


# Yes, the print() is funny. This is
# to test though a 2-arg assert where
# the 2nd argument is not a string.
assert x((("_foo", None),)) == {}, print("See issue #162")

# From 3.7 test_dictcomps.py
assert {k: v for k in range(10) for v in range(10) if k == v} == {
    0: 0,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 9,
}
