# Bug found in 2.7 test_itertools.py
# Bug was erroneously using reduction to unconditional_true
# A proper fix would be to use unconditional_true only when we
# can determine there is or was dead code.
from itertools import izip_longest
for args in [['abc', range(6)]]:
    target = [tuple([arg[i] if i < len(arg) else None for arg in args])
              for i in range(max(map(len, args)))]
    assert list(izip_longest(*args)) ==  target
