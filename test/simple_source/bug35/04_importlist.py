# From 3.7 test_cmath.py
# Had bug in 3.x in not having semantic importlist rule
# bug is treating "import as" as "from xx import" while
# still being able to hand "from xx import" properly

# RUNNABLE!
import os.path as osp
from sys import platform
from os import sep, name
import collections.abc

assert osp.basename("a") == "a"

assert isinstance(platform, str)
assert sep
assert name
assert collections.abc
import os.path as path
assert path
