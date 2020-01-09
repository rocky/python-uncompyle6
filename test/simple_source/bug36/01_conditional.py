# From 3.7.6 test_buffer.py

# RUNNABLE!
def foo(n):
    zero_stride = True if n >= 95 and n & 1 else False
    return zero_stride

assert foo(95)
assert not foo(94)
assert not foo(96)
