#!/usr/bin/env python
""" Trivial helper program to bytecompile and run an uncompile
"""
import os, sys, py_compile
assert len(sys.argv) == 2
path = sys.argv[1]
short = os.path.basename(path)
version = sys.version[0:3]
cfile =  "bytecode_%s/%s" % (version, short) + 'c'
print("byte-compiling %s to %s" % (path, cfile))
py_compile.compile(path, cfile)
os.system("../bin/uncompyle6 -a -t %s" % cfile)
