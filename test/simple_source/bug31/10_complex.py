# Greatly simplified from from 3.3 test_complex.py
from math import atan2

# RUNNABLE!
def assertCloseAbs(x, y, eps=1e-09):
    """Return true iff floats x and y "are close\""""
    if abs(x) > abs(y):
        x, y = y, x
    if y == 0:
        return abs(x) < eps
    if x == 0:
        return abs(y) < eps
    assert abs((x - y) / y) < eps

def assertClose(x, y, eps=1e-09):
    """Return true iff complexes x and y "are close\""""
    assertCloseAbs(x.real, y.real, eps)
    assertCloseAbs(x.imag, y.imag, eps)

def check_div(x, y):
    """Compute complex z=x*y, and check that z/x==y and z/y==x."""
    z = x * y
    if x != 0:
        q = z / x
        assertClose(q, y)
        q = z.__truediv__(x)
        assertClose(q, y)
    if y != 0:
        q = z / y
        assertClose(q, x)
        q = z.__truediv__(y)
        assertClose(q, x)

def test_truediv():
    simple_real = [float(i) for i in range(-5, 6)]
    simple_complex = [complex(x, y) for x in simple_real for y in simple_real]
    for x in simple_complex:
        for y in simple_complex:
            check_div(x, y)

def test_plus_minus_0j():
    assert -0j == -0j == complex(0.0, 0.0)
    assert -0-0j == -0j == complex(0.0, 0.0)
    z1, z2 = (0j, -0j)
    assert atan2(z1.imag, -1.0) == atan2(0.0, -1.0)
    # assert atan2(z2.imag, -1.0), atan2(-0.0, -1.0)

# Check that we can handle -inf, and inf as a complex numbers.
# And put it in a tuple and a list to make it harder.
z1, z2 = (-1e1000j, 1e1000j)
assert z1 in [-1e1000j, 1e1000j]
assert z1 != z2
test_truediv()
test_plus_minus_0j()
