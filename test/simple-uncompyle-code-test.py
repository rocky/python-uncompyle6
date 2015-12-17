#!/usr/bin/env python

from __future__ import print_function

from uncompyle6 import uncompyle
import sys, inspect

def uncompyle_test():
    frame = inspect.currentframe()
    try:
        co = frame.f_code
        uncompyle(2.7, co, sys.stdout, 1, 1)
        print()
    finally:
        del frame

uncompyle_test()
