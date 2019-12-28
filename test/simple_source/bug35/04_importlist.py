# From 3.7 test_cmath.py
# Had bug in 3.x in not having semantic importlist rule
# bug is treating "import as" as "from xx import" while
# still being able to hand "from xx import" properly

# RUNNABLE!
import os.path as osp
from sys import path
from os import sep, name

assert osp.basename("a")
assert path
assert sep
assert name
