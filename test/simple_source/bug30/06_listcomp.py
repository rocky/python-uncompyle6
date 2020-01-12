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

# From 3.7.6 _collections_abc.py
# Bug was handling "or" in listcomp
def count(values, x):
    return sum(1 for v in values if v or x)

assert count([2, 2], False) == 2
assert count([], False) == 0
assert count([], True) == 0
assert count([2], True) == 1
assert count([0], False) == 0

# From 3.7 test_generators
# Bug was in handling the way list_if is optimized in 3.7+;
# We need list_if37 and compare_chained37.
def init_board(c):
    return [io for io in c if 3 <= io < 5]

assert init_board(list(range(6))) == [3, 4]
