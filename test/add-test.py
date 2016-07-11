#!/usr/bin/env python
""" Trivial helper program to bytecompile and run an uncompile
"""
import os, sys, py_compile
assert len(sys.argv) >= 2
version = sys.version[0:3]
for path in sys.argv[1:]:
    short = os.path.basename(path)
    cfile =  "bytecode_%s/%s" % (version, short) + 'c'
    print("byte-compiling %s to %s" % (path, cfile))
    py_compile.compile(path, cfile)
    if isinstance(version, str) or version >= (2, 6, 0):
        os.system("../bin/uncompyle6 -a -t %s" % cfile)
