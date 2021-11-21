"""This program is self-checking!"""


def lcase(s):
    return s.lower()


l = ["xyz", "ABC"]
l.sort(key=lcase)
assert l == ["ABC", "xyz"]
