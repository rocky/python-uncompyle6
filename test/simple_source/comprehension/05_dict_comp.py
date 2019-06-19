# Bug was in dictionary comprehension involving "if not"
# Issue #162
#
# This code is RUNNABLE!
def x(s):
    return {k: v
            for (k, v) in s
            if not k.startswith('_')
    }

# Yes, the print() is funny. This is
# to test though a 2-arg assert where
# the 2nd argument is not a string.
assert x((('_foo', None),)) == {}, print("See issue #162")
