#!/usr/bin/env python
# Mode: -*- python -*-
#
# Copyright (c) 2015 by Rocky Bernstein <rb@dustyfeet.com>
#
from __future__ import print_function


import dis, os.path

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

program =  os.path.basename(__file__)

__doc__ = """
Usage: %s [OPTIONS]... FILE

""" % program

usage_short = "Usage: %s [OPTIONS]... FILE" % program

import uncompyle6
from uncompyle6 import PYTHON_VERSION_STR, check_python_version
from uncompyle6.disas import disco

def inst_fmt(inst):
    if inst.starts_line:
        return '\n%4d  %6s\t%-17s %r' % (inst.starts_line, inst.offset, inst.opname,
                                         inst.argrepr)
    else:
        return '      %6s\t%-17s %r' % (inst.offset, inst.opname, inst.argrepr)

    print
    return

def compare_ok(version, co):
    out  = StringIO()
    if version in (2.6, 2.7):
        print("Doesn't work on %d\n yet"  %  version)
        # dis.disco(co)
        return True

    bytecode = dis.Bytecode(co)

    disco(version, co, out)
    got_lines = out.getvalue().split("\n")[2:]
    i = 0
    good_lines = "\n".join([inst_fmt(inst) for inst in bytecode]).split("\n")
    for good_line in good_lines:
        if '\tCOME_FROM         ' in got_lines[i]:
            i += 1

        if got_lines[i] != good_line:
            print('line %d %s' % (i+1, ('=' * 30)))
            print(good_line)
            print("vs %s" % ('-' * 10))
            print(got_lines[i])
            return False
        i += 1
    return True

check_python_version(program)

# if len(sys.argv) != 2:
#     print(usage_short, file=sys.stderr)
#     sys.exit(1)

# filename = sys.arv[1]
def get_srcdir():
    filename = os.path.normcase(os.path.dirname(__file__))
    return os.path.realpath(filename)

src_dir = get_srcdir()
os.chdir(src_dir)

files=[
    'if',
    'ifelse',
    # 'keyword',
    ]

for base in files:
    filename = "bytecode_%s/%s.pyc" % (PYTHON_VERSION_STR, base)
    version, timestamp, magic_int, co = uncompyle6.load_module(filename)
    ok = True

    if type(co) == list:
        for con in co:
            ok = compare_ok(version, con)
            if not ok: break
    else:
        ok = compare_ok(version, co)
    if ok:
        print("Disassembly of %s checks out!" % filename)
    else:
        print("Disassembly of %s mismatches." % filename)
        break
