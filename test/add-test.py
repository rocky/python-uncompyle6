#!/usr/bin/env python
""" Trivial helper program to bytecompile and run an uncompile
"""
import os, sys, py_compile

assert len(sys.argv) >= 2
version = sys.version[0:3]
vers = sys.version_info[:2]
if sys.argv[1] in ("--run", "-r"):
    suffix = "_run"
    py_source = sys.argv[2:]
else:
    suffix = ""
    py_source = sys.argv[1:]

for path in py_source:
    short = os.path.basename(path)
    if hasattr(sys, "pypy_version_info"):
        cfile = "bytecode_pypy%s%s/%s" % (version, suffix, short) + "c"
    else:
        cfile = "bytecode_%s%s/%s" % (version, suffix, short) + "c"
    print("byte-compiling %s to %s" % (path, cfile))
    optimize = 2
    if vers >= (3, 0):
        py_compile.compile(path, cfile, optimize=optimize)
    else:
        py_compile.compile(path, cfile)
    if vers >= (2, 6):
        os.system("../bin/uncompyle6 -a -T %s" % cfile)
