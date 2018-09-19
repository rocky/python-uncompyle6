#!/usr/bin/env python

from __future__ import print_function

from uncompyle6.main import decompile
from xdis.magics import sysinfo2float
import sys, inspect

def uncompyle_test():
    frame = inspect.currentframe()
    try:
        co = frame.f_code
        decompile(sysinfo2float(), co, sys.stdout, 1, 1)
        print()
    finally:
        del frame

uncompyle_test()
