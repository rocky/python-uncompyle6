# Issue 104
# Python 3.8 reverses the order or keys and values in
# dictionary comprehensions from the order in all previous Pythons.
# Also we were looking in the wrong place for the collection of the
# dictionary comprehension
# RUNNABLE!

"""This program is self-checking!"""
x = [(0, [1]), (2, [3])]
for i in range(0, 1):
    y = {key: val[i - 1] for (key, val) in x}
assert y == {0: 1, 2: 3}
