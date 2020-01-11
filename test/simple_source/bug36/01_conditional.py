# From 3.7.6 test_buffer.py

# RUNNABLE!
def foo(n):
    zero_stride = True if n >= 95 and n & 1 else False
    return zero_stride

assert foo(95)
assert not foo(94)
assert not foo(96)

# from test_buffer.py
# Bug was handling "or" inside a conditional
def rslice(a, b):
    minlen = 0 if a or b else 1
    return minlen

assert rslice(False, False) == 1
assert rslice(False, True) == 0
assert rslice(True, False) == 0
assert rslice(True, True) == 0
