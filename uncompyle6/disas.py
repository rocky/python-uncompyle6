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

import sys
from collections import deque

import uncompyle6

from xdis.main import disassemble_file as xdisassemble_file
from xdis.code import iscode
from xdis.load import check_object_path, load_module
from uncompyle6.scanner import get_scanner

def disco(version, co, out=None, is_pypy=False):
    """
    diassembles and deparses a given code block 'co'
    """

    assert iscode(co)

    # store final output stream for case of error
    real_out = out or sys.stdout
    real_out.write('# Python %s\n' % version)
    if co.co_filename:
        real_out.write('# Embedded file name: %s\n' % co.co_filename)

    scanner = get_scanner(version, is_pypy=is_pypy)

    queue = deque([co])
    disco_loop(scanner.ingest, queue, real_out)


def disco_loop(disasm, queue, real_out):
    while len(queue) > 0:
        co = queue.popleft()
        if co.co_name != '<module>':
            real_out.write('\n# %s line %d of %s\n' %
                      (co.co_name, co.co_firstlineno, co.co_filename))
        tokens, customize = disasm(co)
        for t in tokens:
            if iscode(t.pattr):
                queue.append(t.pattr)
            elif iscode(t.attr):
                queue.append(t.attr)
            real_out.write(t)
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
    (version, timestamp, magic_int, co, is_pypy,
     source_size) = load_module(filename)
    if type(co) == list:
        for con in co:
            disco(version, con, outstream)
    else:
        disco(version, co, outstream, is_pypy=is_pypy)
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
