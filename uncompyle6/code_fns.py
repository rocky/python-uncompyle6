#  Copyright (c) 2015-2016, 2818-2022, 2024 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
CPython magic- and version-independent disassembly routines

There are two reasons we can't use Python's built-in routines
from ``dis``.

First, the bytecode we are extracting may be from a different
version of Python (different magic number) than the version of Python
that is doing the extraction.

Second, we need structured instruction information for the
(de)-parsing step. Python 3.4 and up provides this, but we still do
want to run on earlier Python versions.
"""

import sys
from collections import deque

from xdis import check_object_path, iscode, load_module
from xdis.version_info import version_tuple_to_str
from uncompyle6.scanner import get_scanner


def disco(version, co, out=None, is_pypy=False):
    """
    disassembles and deparses a given code block ``co``.
    """

    assert iscode(co)

    # Store final output stream in case there is an error.
    real_out = out or sys.stdout
    print("# Python %s" % version_tuple_to_str(version), file=real_out)
    if co.co_filename:
        print("# Embedded file name: %s" % co.co_filename, file=real_out)

    scanner = get_scanner(version, is_pypy=is_pypy)

    queue = deque([co])
    disco_loop(scanner.ingest, queue, real_out)


def disco_loop(disasm, queue, real_out):
    while len(queue) > 0:
        co = queue.popleft()
        if co.co_name != "<module>":
            if hasattr(co, "co_firstlineno"):
                print(
                    "\n# %s line %d of %s"
                    % (co.co_name, co.co_firstlineno, co.co_filename),
                    file=real_out,
                )
            else:
                print(
                    "\n# %s of %s"
                    % (co.co_name, co.co_filename),
                    file=real_out,
                )
        tokens, customize = disasm(co)
        for t in tokens:
            if iscode(t.pattr):
                queue.append(t.pattr)
            elif iscode(t.attr):
                queue.append(t.attr)
            print(t, file=real_out)
            pass
        pass


# def disassemble_fp(fp, outstream=None):
#     """
#     disassemble Python byte-code from an open file
#     """
#     (version, timestamp, magic_int, co, is_pypy,
#      source_size) = load_from_fp(fp)
#     if type(co) == list:
#         for con in co:
#             disco(version, con, outstream)
#     else:
#         disco(version, co, outstream, is_pypy=is_pypy)
#     co = None


def disassemble_file(filename, outstream=None):
    """
    Disassemble Python byte-code file (.pyc).

    If given a Python source file (".py") file, we'll
    try to find the corresponding compiled object.
    """
    filename = check_object_path(filename)
    (version, timestamp, magic_int, co, is_pypy, source_size, sip_hash) = load_module(
        filename
    )
    if type(co) == list:
        for con in co:
            disco(version, con, outstream)
    else:
        disco(version, co, outstream, is_pypy=is_pypy)


def _test():
    """Simple test program to disassemble a file."""
    argc = len(sys.argv)
    if argc != 2:
        if argc == 1:
            fn = __file__
        else:
            sys.stderr.write("usage: %s [-|CPython compiled file]\n" % __file__)
            sys.exit(2)
    else:
        fn = sys.argv[1]
    disassemble_file(fn)


if __name__ == "__main__":
    _test()
