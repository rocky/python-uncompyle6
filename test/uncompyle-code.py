#!/usr/bin/env python

from __future__ import print_function

import uncompyle6
from uncompyle6 import uncompyle, walker, verify, magics
from uncompyle6.spark import GenericASTTraversal, GenericASTTraversalPruningException
import sys, inspect, types

if (sys.version_info > (3, 0)):
    from io import StringIO
else:
    from StringIO import StringIO

from collections import namedtuple
NodeInfo = namedtuple("NodeInfo", "node start finish")

def uncompyle_test():
    frame = inspect.currentframe()
    try:
        co = frame.f_code
        uncompyle(2.7, co, sys.stdout, 1, 1)
        print()
    finally:
        del frame

uncompyle_test()
