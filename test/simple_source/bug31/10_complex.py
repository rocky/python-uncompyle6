# Greatly simplified from from 3.3 test_complex.py

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

z2 = -1e1000j # Check that we can handle -inf as a complex number
test_truediv()
