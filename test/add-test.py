#!/usr/bin/env python
""" Trivial helper program to byte compile and uncompile the bytecode file.
"""
import os, sys, py_compile
from xdis.version_info import version_tuple_to_str, PYTHON_VERSION_TRIPLE

if len(sys.argv) < 2:
    print("Usage: add-test.py [--run] *python-source*... [optimize-level]")
    sys.exit(1)

assert 2 <= len(sys.argv) <= 4
version = sys.version[0:3]
vers = sys.version_info[:2]
if sys.argv[1] in ("--run", "-r"):
    suffix = "_run"
    assert len(sys.argv) >= 3
    py_source = sys.argv[2:]
    i = 2
else:
    suffix = ""
    py_source = sys.argv[1:]
    i = 1
try:
    optimize = int(sys.argv[-1])
    assert sys.argv >= i + 2
    py_source = sys.argv[i:-1]
    i = 2

except:
    optimize = 2

for path in py_source:
    short = os.path.basename(path)
    if short.endswith(".py"):
        short = short[: -len(".py")]
    if hasattr(sys, "pypy_version_info"):
        version = version_tuple_to_str(end=2, delimiter="")
        bytecode = "bytecode_pypy%s%s/%spy%s.pyc" % (version, suffix, short, version)
    else:
        version = version_tuple_to_str(end=2)
        bytecode = "bytecode_%s%s/%s.pyc" % (version, suffix, short)

    print("byte-compiling %s to %s" % (path, bytecode))
    if PYTHON_VERSION_TRIPLE >= (3, 2):
        py_compile.compile(path, bytecode, optimize=optimize)
    else:
        py_compile.compile(path, bytecode)
    if PYTHON_VERSION_TRIPLE >= (2, 6):
        os.system("../bin/uncompyle6 -a -t %s" % bytecode)
