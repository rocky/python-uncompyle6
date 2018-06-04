#!/usr/bin/env python
"""byte compiles a Python 1.x program"""
import sys
if len(sys.argv) != 2:
    print("Usage: compile-file.py *python-file*")
    sys.exit(1)
source = sys.argv[1]

# assert source.endswith('.py')
basename = source[:-3]

# We do this crazy way to support Python 1.4 which
# doesn't support version_info.
PY_VERSION = sys.version[:3]

bytecode = "%s-%s.pyc" % (basename, PY_VERSION)

import py_compile
print("# compiling %s to %s" % (source, bytecode))
py_compile.compile(source, bytecode)
# import os
# os.system("../bin/uncompyle6 %s" % bytecode)
