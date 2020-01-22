if __file__:
    0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0+0


# From 3.7 test_buffer.py
# Bug is in dealing with EXTENDED_ARG instructions.
# In reduction-rule tests where we are testing the offset,
# getting *which* offset to test against, when there are two
# possible offset, can mess us up.

def five(a):
    return 5

def test_ndarray_slice_multidim(a, f, listerr):
    for slices in a:
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 1
        shape_t = 2
        shape_t = 3
        shape_t = 4
        shape_t = 5
        shape_t = 6
        shape_t = 7
        shape_t = 8
        shape_t = 9
        nderr = None
        if nderr or listerr:
            return f(5)
        else:
            return 2

assert test_ndarray_slice_multidim([1], five, False) == 2
assert test_ndarray_slice_multidim([1], five, True) == 5
