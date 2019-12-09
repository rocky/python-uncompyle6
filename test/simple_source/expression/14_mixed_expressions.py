# Covers a large number of operators
#
# This code is RUNNABLE!

import sys
PYTHON_VERSION = sys.version_info[0] + (sys.version_info[1] / 10.0)

assert PYTHON_VERSION >= 3.7

# some floats (from 01_float.py)

x = 1e300
assert 0.0 == x * 0
assert x * 1e300 == float("inf")
assert str(float("inf") * 0.0) == "nan"
assert str(float("-inf") * 0.0) == "nan"
assert -1e300 * 1e300 == float("-inf")

# Complex (adapted from 02_complex.py)
y = 5j
assert y ** 2 == -25
y **= 3
assert y == (-0-125j)


# Tests BINARY_TRUE_DIVIDE and INPLACE_TRUE_DIVIDE (from 02_try_divide.py)
x = 2
assert 4 / x == 2

x = 5
assert x / 2 == 2.5
x = 3
x /= 2
assert x == 1.5

x = 2
assert 4 // x == 2
x = 7
x //= 2
assert x == 3

x = 3
assert x % 2 == 1
x %= 2
assert x == 1

assert x << 2 == 4
x <<= 3
assert x == 8

assert x >> 1 == 4
x >>= 1
assert x == 4
