# Tests all the different kinds of imports
"""This program is self-checking!"""

import sys
from os import path
from os import *  # NOQA

import time as time1, os as os1

assert isinstance(os1.pathsep, str)

assert time1.time() > 0
import os.path as osp

assert osp == path
from os.path import join as jj

assert path.join("a", "b") == jj("a", "b")

if len(__file__) == 0:
    # a.b.c should force consecutive LOAD_ATTRs
    import stuff0.stuff1.stuff2.stuff3 as stuff3

sys.exit(0)
