#!/usr/bin/env python
""" Trivial helper program to bytecompile and run an uncompile
"""
import os, sys, py_compile

assert (2 <= len(sys.argv) <= 4)
version = sys.version[0:3]
vers = sys.version_info[:2]
if sys.argv[1] in ("--run", "-r"):
    suffix = "_run"
    py_source = sys.argv[2:]
    i = 2
else:
    suffix = ""
    py_source = sys.argv[1:]
    i = 1
try:
    optimize = int(sys.argv[-1])
    py_source = sys.argv[i:-1]
except:
    optimize = 2

for path in py_source:
    short = os.path.basename(path)
    if hasattr(sys, "pypy_version_info"):
        cfile = "bytecode_pypy%s%s/%s" % (version, suffix, short) + "c"
    else:
        cfile = "bytecode_%s%s/%s" % (version, suffix, short) + "c"
    print("byte-compiling %s to %s" % (path, cfile))
    optimize = optimize
    if vers > (3, 1):
        py_compile.compile(path, cfile, optimize=optimize)
    else:
        py_compile.compile(path, cfile)
    if vers >= (2, 6):
        os.system("../bin/uncompyle6 -a -T %s" % cfile)
