#!/usr/bin/env python
#
#  Copyright (c) 2015-2016, 2018, 2020, 2022-2024
#  by Rocky Bernstein <rb@dustyfeet.com>
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
#

import getopt
import os
import sys

from uncompyle6.code_fns import disassemble_file
from uncompyle6.version import __version__

program, ext = os.path.splitext(os.path.basename(__file__))

__doc__ = """
Usage:
  {0} [OPTIONS]... FILE
  {0} [--help | -h | -V | --version]

Disassemble/Tokenize FILE with in the way that is done to
assist uncompyle6 in parsing the instruction stream. For example
instructions with variable-length arguments like CALL_FUNCTION and
BUILD_LIST have argument counts appended to the instruction name, and
COME_FROM pseudo instructions are inserted into the instruction stream.
Bit flag values encoded in an operand are expanding, EXTENDED_ARG
value are folded into the following instruction operand.

Like the parser, you may find this more high-level and or helpful.
However if you want a true disassembler see the Standard built-in
Python library module "dis", or pydisasm from the cross-version
Python bytecode package "xdis".

Examples:
  {0} foo.pyc
  {0} foo.py    # same thing as above but find the file
  {0} foo.pyc bar.pyc  # disassemble foo.pyc and bar.pyc

See also `pydisasm' from the `xdis' package.

Options:
  -V | --version     show version and stop
  -h | --help        show this message

""".format(
    program
)

PATTERNS = ("*.pyc", "*.pyo")


def main():
    usage_short = (
        f"""usage: {program} FILE...
Type -h for for full help."""
    )

    if len(sys.argv) == 1:
        print("No file(s) given", file=sys.stderr)
        print(usage_short, file=sys.stderr)
        sys.exit(1)

    try:
        opts, files = getopt.getopt(
            sys.argv[1:], "hVU", ["help", "version", "uncompyle6"]
        )
    except getopt.GetoptError as e:
        print(f"{os.path.basename(sys.argv[0])}: {e}", file=sys.stderr)
        sys.exit(-1)

    for opt, val in opts:
        if opt in ("-h", "--help"):
            print(__doc__)
            sys.exit(1)
        elif opt in ("-V", "--version"):
            print(f"{program} {__version__}")
            sys.exit(0)
        else:
            print(opt)
            print(usage_short, file=sys.stderr)
            sys.exit(1)

    for file in files:
        if os.path.exists(files[0]):
            disassemble_file(file, sys.stdout)
        else:
            print(f"Can't read {files[0]} - skipping", file=sys.stderr)
            pass
        pass
    return


if __name__ == "__main__":
    main()
