# Self-checking test.
# String interpolation tests

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

# From 3.6 http/client.py
# Bug is in handling  X
chunk = ['a', 'b', 'c']
chunk2 = 'd'
chunk = f'{len(chunk):X}' + chunk2
assert chunk == '3d'

chunk = b'abc'
chunk2 = 'd'
chunk = f'{len(chunk):X}\r\n'.encode('ascii') + chunk \
        + b'\r\n'
assert chunk == b'3\r\nabc\r\n'

# From 3.6.8 idlelib/pyshell.py
# Bug was handling '''
import os
filename = '.'
source = 'foo'
source = (f"__file__ = r'''{os.path.abspath(filename)}'''\n"
          + source + "\ndel __file__")
print(source)
