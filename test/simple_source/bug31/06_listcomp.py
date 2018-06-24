# Python 3.0 comprehensions can produce different code from
# all other Python versions. Thanks, Python!

# Adapted from 3.0 ast.py
# This code is RUNNABLE!
def _format(node):
    return [(a, int(b)) for a, b in node.items()]

# Adapted from 3.0 cmd.py
def monthrange(ary, dotext):
    return [a[3:] for a in ary if a.startswith(dotext)]

x = {'a': '1', 'b': '2'}
assert [('a', 1), ('b', 2)] == _format(x)

ary = ["Monday", "Twoday", "Monmonth"]
assert ['day', 'month'] == monthrange(ary, "Mon")
