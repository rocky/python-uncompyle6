# Bug was in dictionary comprehension involving "if not"
# Issue #162
#
# This code is RUNNABLE!
def x(s):
    return {k: v
            for (k, v) in s
            if not k.startswith('_')
    }

assert x((('_foo', None),)) == {}
