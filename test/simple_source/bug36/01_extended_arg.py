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
        shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
        shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
        shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
        shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
        shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
        nderr = None
        if nderr or listerr:
            return f(5)
        else:
            return 2

assert test_ndarray_slice_multidim([1], five, False) == 2
assert test_ndarray_slice_multidim([1], five, True) == 5

# From 3.7 test_builtin.py
def test_pow(self, m, a, b, c, f):

    shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
    shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
    shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
    shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
    shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
    shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9

    shape_t = 0; shape_t = 1; shape_t = 2;

    for z in m:
        if a or \
           b or \
           c:
            f(TypeError)
        else:
            x = 2

    x = 3

# From 3.7 test_exceptions.py
# Bug is handling extended arg
def testAttributes(exceptionList):
    try:
        x = 0
    except:
        pass

    for exc in exceptionList:
        x = 0; x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8; x = 9;
        x = 0; x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8; x = 9;
        x = 0; x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8; x = 9;
        x = 0; x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8; x = 9;
        x = 0; x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8; x = 9;
        x = 0; x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8; x = 9;
        x = 0

# From test_urllibnet2.py
# Bug was in detecting end of "if" flowing into an extended-arg "for".
def _test_urls(retry, urls):
    if retry:
        urlopen = 1

    for url in urls:
        shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
        shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
        shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
        shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
        shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
        shape_t = 0; shape_t = 1; shape_t = 2; shape_t = 3; shape_t = 4; shape_t = 5; shape_t = 6; shape_t = 7; shape_t = 8; shape_t = 9
        shape_t = 0
