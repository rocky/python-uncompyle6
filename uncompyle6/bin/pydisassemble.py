#!/usr/bin/env python
# Mode: -*- python -*-
#
# Copyright (c) 2015-2016, 2018 by Rocky Bernstein <rb@dustyfeet.com>
#
from __future__ import print_function
import sys, os, getopt

from uncompyle6.disas import disassemble_file
from uncompyle6.version import VERSION

program, ext = os.path.splitext(os.path.basename(__file__))

__doc__ = """
Usage:
  {0} [OPTIONS]... FILE
  {0} [--help | -h | -V | --version]

Disassemble FILE with the instruction mangling that is done to
assist uncompyle6 in parsing the instruction stream. For example
instructions with variable-length arguments like CALL_FUNCTION and
BUILD_LIST have arguement counts appended to the instruction name, and
COME_FROM instructions are inserted into the instruction stream.

Examples:
  {0} foo.pyc
  {0} foo.py    # same thing as above but find the file
  {0} foo.pyc bar.pyc  # disassemble foo.pyc and bar.pyc

See also `pydisasm' from the `xdis' package.

Options:
  -V | --version     show version and stop
  -h | --help        show this message

""".format(program)

PATTERNS = ('*.pyc', '*.pyo')

def main():
    Usage_short = """usage: %s FILE...
Type -h for for full help.""" % program

    if len(sys.argv) == 1:
        print("No file(s) given", file=sys.stderr)
        print(Usage_short, file=sys.stderr)
        sys.exit(1)

    try:
        opts, files = getopt.getopt(sys.argv[1:], 'hVU',
                                    ['help', 'version', 'uncompyle6'])
    except getopt.GetoptError as e:
        print('%s: %s' % (os.path.basename(sys.argv[0]), e),  file=sys.stderr)
        sys.exit(-1)

    for opt, val in opts:
        if opt in ('-h', '--help'):
            print(__doc__)
            sys.exit(1)
        elif opt in ('-V', '--version'):
            print("%s %s" % (program, VERSION))
            sys.exit(0)
        else:
            print(opt)
            print(Usage_short, file=sys.stderr)
            sys.exit(1)

    for file in files:
        if os.path.exists(files[0]):
            disassemble_file(file, sys.stdout)
        else:
            print("Can't read %s - skipping" % files[0],
                  file=sys.stderr)
            pass
        pass
    return

if __name__ == '__main__':
    main()
