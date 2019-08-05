# Issue #283 in Python 2.6
# See https://github.com/rocky/python-uncompyle6/issues/283

# This code is RUNNABLE!

G = ( c for c in "spam, Spam, SPAM!" if c > 'A' and c < 'S')
assert list(G) == ["P", "M"]
