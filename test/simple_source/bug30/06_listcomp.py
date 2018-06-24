# Python 3.0 comprehensions can produce different code from
# all other Python versions. Thanks, Python!

# This code is RUNNABLE!

# Adapted from 3.0 ast.py; uses comprehension implemented via CLOSURE
def _format(node):
    return [(a, int(b)) for a, b in node.items()]

x = {'a': '1', 'b': '2'}
assert [('a', 1), ('b', 2)] == _format(x)

# Adapted from 3.0 cmd.py; ises "if" comprehension
def monthrange(ary, dotext):
    return [a[3:] for a in ary if a.startswith(dotext)]

ary = ["Monday", "Twoday", "Monmonth"]
assert ['day', 'month'] == monthrange(ary, "Mon")

# From 3.0 cmd.py; uses "if not" comprehension
def columnize(l):
    return [i for i in range(len(l))
            if not isinstance(l[i], str)]
assert [0, 2] == columnize([1, 'a', 2])
