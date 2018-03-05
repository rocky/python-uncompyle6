# Issue #162
def x(s):
    return {k: v
            for (k, v) in s
            if not k.startswith('_')
    }

assert x((('_foo', None),)) == {}
