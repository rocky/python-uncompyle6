# Self-checking test.
# String interpolation tests

# RUNNABLE!
"""This program is self-checking!"""

var1 = "x"
var2 = "y"
abc = "def"
assert (
    f"interpolate {var1} strings {var2!r} {var2!s} 'py36"
    == "interpolate x strings 'y' y 'py36"
)
assert "def0" == f"{abc}0"
assert "defdef" == f"{abc}{abc!s}"

# From 3.8 test/test_string.py
# We had the precedence of yield vs. lambda incorrect.
def fn(x):
    yield f"x:{yield (lambda i: x * i)}"


# From 3.6 functools.py
# Bug was handling format operator strings.

k, v = "1", ["2"]
x = f"{k}={v!r}"
y = f"functools.{x}({', '.join(v)})"
assert x == "1=['2']"
assert y == "functools.1=['2'](2)"

# From 3.6 http/client.py
# Bug is in handling  X
chunk = ["a", "b", "c"]
chunk2 = "d"
chunk = f"{len(chunk):X}" + chunk2
assert chunk == "3d"

chunk = b"abc"
chunk2 = "d"
chunk = f"{len(chunk):X}\r\n".encode("ascii") + chunk + b"\r\n"
assert chunk == b"3\r\nabc\r\n"

# From 3.6.8 idlelib/pyshell.py
# Bug was handling '''
import os

filename = "."
source = "foo"
source = f"__file__ = r'''{os.path.abspath(filename)}'''\n" + source + "\ndel __file__"

# Note how { and } are *not* escaped here
f = "one"
name = "two"
assert (f"{f}{'{{name}}'} {f}{'{name}'}") == "one{{name}} one{name}"

# From 3.7.3 dataclasses.py
log_rounds = 5
assert "05$" == f"{log_rounds:02d}$"


def testit(a, b, ll):
    # print(ll)
    return ll


# The call below shows the need for BUILD_STRING to count expr arguments.
# Also note that we use {{ }} to escape braces in contrast to the example
# above.
def _repr_fn(fields):
    return testit(
        "__repr__",
        ("self",),
        ['return xx + f"(' + ", ".join([f"{f}={{self.{f}!r}}" for f in fields]) + ')"'],
    )


fields = ["a", "b", "c"]
assert _repr_fn(fields) == ['return xx + f"(a={self.a!r}, b={self.b!r}, c={self.c!r})"']


#################################
# From Python 3.7 test_fstring.py

x = 5
assert f'{(lambda y:x*y)("8")!r}' == "'88888'"
assert f'{(lambda y:x*y)("8")!r:10}' == "'88888'   "
assert f'{(lambda y:x*y)("8"):10}' == "88888     "

try:
    eval("f'{lambda x:x}'")
except SyntaxError:
    pass
else:
    assert False, "f'{lambda x:x}' should be a syntax error"

(x, y, width) = ("foo", 2, 10)
assert f"x={x*y:{width}}" == "x=foofoo    "

# Why the fact that the distinction of docstring versus stmt is a
# string expression is important academic, but we will decompile an
# equivalent thing. For compatiblity with older Python we'll use "%"
# instead of a format string
def f():
    f"""Not a docstring"""  # noqa


def g():
    """Not a docstring""" f""  # noqa


assert f.__doc__ is None
assert g.__doc__ is None

import decimal

width, precision, value = (10, 4, decimal.Decimal("12.34567"))

# Make sure we don't have additional f'..' inside the format strings below.
assert f"result: {value:{width}.{precision}}" == "result:      12.35"
assert f"result: {value:{width:0}.{precision:1}}" == "result:      12.35"
assert f"{2}\t" == "2\t"

# But below we *do* need the additional f".."
assert f'{f"{0}"*3}' == "000"

# We need to make sure we have { {x:... not {{x: ...
#                               ^
# The former, {{ confuses the format strings so dictionary/set comprehensions
# don't work.
assert f"expr={ {x: y for x, y in [(1, 2), ]}}" == "expr={1: 2}"


class Line:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    # From 3.7 test_typing.py
    def __str__(self):
        return f"{self.x} -> {self.y}"


line = Line(1, 2)
assert str(line) == "1 -> 2"
