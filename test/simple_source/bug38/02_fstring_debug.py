# Tests new "debug" format new in 3.8.
# Much of this is adapted from 3.8 test/test_fstring.py
# RUNNABLE!

"""This program is self-checking!"""

# fmt: off
# We want to use "=" and ":=" *without* the surrounding space to test format spec and "=" detection
f'{f"{3.1415=:.1f}":*^20}' == '*****3.1415=3.1*****'

y = 2
def f(x, width):
    return f'x={x*y:{width}}'

assert f('foo', 10) ==  'x=foofoo    '

x = 'bar'
assert f(10, 10), 'x=        20'

x = 'A string'
f"x={x!r}" == 'x=' + repr(x)

pi = 'π'
assert f'alpha α {pi=} ω omega', "alpha α pi='π' ω omega"

x = 20
# This isn't an assignment expression, it's 'x', with a format
# spec of '=10'.
assert f'{x:=10}' ==  '        20'

assert f'{(x:=10)}' ==  '10'
assert x ==  10
