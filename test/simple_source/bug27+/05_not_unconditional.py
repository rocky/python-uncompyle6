# From 2.7 test_itertools.py
# Bug was in 2.7 decompiling like the commented out
# code below
from itertools import izip_longest
for args in [
        ['abc', range(6)],
        ]:
    # target = [tuple([ arg[i] if 1 else None for arg in args if i < len(arg) ])
    #          for i in range(max(map(len, args)))]
    target = [tuple([arg[i] if i < len(arg) else None for arg in args])
              for i in range(max(map(len, args)))]
    assert list(izip_longest(*args)) == target
