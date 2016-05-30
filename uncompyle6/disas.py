# Copyright (c) 2015-2016 by Rocky Bernstein
# Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
# Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
# Copyright (c) 1999 John Aycock

"""
CPython magic- and version- independent disassembly routines

There are two reasons we can't use Python's built-in routines
from dis. First, the bytecode we are extracting may be from a different
version of Python (different magic number) than the version of Python
that is doing the extraction.

Second, we need structured instruction information for the
(de)-parsing step. Python 3.4 and up provides this, but we still do
want to run on Python 2.7.
"""

from __future__ import print_function

import datetime, sys
from collections import deque

import uncompyle6

from xdis.main import disassemble_file as xdisassemble_file
from xdis.util import format_code_info
from xdis.code import iscode
from xdis.load import check_object_path, load_module
from uncompyle6 import PYTHON_VERSION
from uncompyle6.scanner import get_scanner


def disco(version, co, timestamp, out=None):
    """
    diassembles and deparses a given code block 'co'
    """

    assert iscode(co)

    out.write('# Python bytecode %s (disassembled from Python %s)\n' %
              (version, PYTHON_VERSION))
    if timestamp > 0:
        value = datetime.datetime.fromtimestamp(timestamp)
        out.write(value.strftime('# Timestamp in code: '
                                 '%Y-%m-%d %H:%M:%S\n'))

    # store final output stream for case of error
    real_out = out or sys.stdout

    if co.co_filename:
        print('# Embedded file name: %s' % co.co_filename,
              file=real_out)

    scanner = get_scanner(version)

    queue = deque([co])
    disco_loop(scanner.disassemble, version, queue, real_out)


def disco_loop(disasm, version, queue, real_out):
    while len(queue) > 0:
        co = queue.popleft()

        print(format_code_info(co, version), file=real_out)

        tokens, customize = disasm(co)
        for t in tokens:
            if iscode(t.pattr):
                queue.append(t.pattr)
            elif iscode(t.attr):
                queue.append(t.attr)
            print(t.format(), file=real_out)
            pass
        pass

def disassemble_file(filename, outstream=None, native=False):
    """
    disassemble Python byte-code file (.pyc)

    If given a Python source file (".py") file, we'll
    try to find the corresponding compiled object.
    """

    if native:
        xdisassemble_file(filename, outstream)
        return
    filename = check_object_path(filename)
    version, timestamp, magic_int, co = load_module(filename)
    if type(co) == list:
        for con in co:
            disco(version, con, outstream, native)
    else:
        disco(version, co, timestamp, outstream)
    co = None

def _test():
    """Simple test program to disassemble a file."""
    argc = len(sys.argv)
    if argc != 2:
        if argc == 1 and uncompyle6.PYTHON3:
            fn = __file__
        else:
            sys.stderr.write("usage: %s [-|CPython compiled file]\n" % __file__)
            sys.exit(2)
    else:
        fn = sys.argv[1]
    disassemble_file(fn, native=True)

if __name__ == "__main__":
    _test()
