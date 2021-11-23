"""This program is self-checking!"""


class C:
    def sort(self, l, reverse, key_fn):
        # PyPy example of CALL_METHOD_KW 2
        # 2 keyword arguments and no positional arguments
        return l.sort(reverse=reverse, key=key_fn)


def lcase(s):
    return s.lower()


x = C()
l = ["xyz", "ABC"]

# An PyPy example of CALL_METHOD_KW 3
# 2 keyword arguments and one positional argument
x.sort(l, reverse=False, key_fn=lcase)
assert l == ["ABC", "xyz"]
