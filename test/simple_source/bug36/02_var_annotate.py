# 3.6+ type annotations on variables
from typing import List

# RUNNABLE!
y = 2
x: bool
z: int = 5
x = (z == 5)
assert x
assert y == 2
v: List[int] = [1, 2]
assert v[1] == y
