# Self-checking 3.6+ string interpolation tests

var1 = 'x'
var2 = 'y'
abc  = 'def'
assert (f'interpolate {var1} strings {var2!r} {var2!s} py36' ==
        "interpolate x strings 'y' y py36")
assert 'def0' == f'{abc}0'
assert 'defdef' == f'{abc}{abc!s}'

# From 3.6 functools.py
# Bug was handling format operator strings.

k, v = "1", ["2"]
x = f"{k}={v!r}"
y = f"functools.{x}({', '.join(v)})"
assert x == "1=['2']"
assert y == "functools.1=['2'](2)"
