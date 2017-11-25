#!/usr/bin/env python
import sys
if len(sys.argv) != 2:
    print("Usage: compile-file.py *python-file*")
    sys.exit(1)
source = sys.argv[1]

assert source.endswith('.py')
basename = source[:-3]

# We do this crazy way to support Python 2.6 which
# doesn't support version_major, and has a bug in
# floating point so we can't divide 26 by 10 and get
# 2.6
PY_VERSION = sys.version_info[0] + (sys.version_info[1] / 10.0)

bytecode = "%s-%s.pyc" % (basename, PY_VERSION)

import py_compile
print("compiling %s to %s" % (source, bytecode))
py_compile.compile(source, bytecode, 'exec')
# import os
# os.system("../bin/uncompyle6 %s" % bytecode)
