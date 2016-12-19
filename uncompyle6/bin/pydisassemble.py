#!/usr/bin/env python
# Mode: -*- python -*-
#
# Copyright (c) 2015-2016 by Rocky Bernstein <rb@dustyfeet.com>
#
from __future__ import print_function
import sys, os, getopt

from uncompyle6.disas import disassemble_file
from uncompyle6.version import VERSION

program, ext = os.path.splitext(os.path.basename(__file__))

__doc__ = """
Usage:
  %s [OPTIONS]... FILE
  %s [--help | -h | -V | --version]

Examples:
  {0} foo.pyc
  {0} foo.py    # same thing as above but find the file
  {0} foo.pyc bar.pyc  # disassemble foo.pyc and bar.pyc

Options:
  -U | --uncompyle6  show instructions with uncompyle6 mangling
  -V | --version     show version and stop
  -h | --help        show this message

""".format(program)

PATTERNS = ('*.pyc', '*.pyo')

def main():
    Usage_short = """usage: %s FILE...
Type -h for for full help.""" % program

    native = True

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
        elif opt in ('-U', '--uncompyle6'):
            native = False
        else:
            print(opt)
            print(Usage_short, file=sys.stderr)
            sys.exit(1)

    for file in files:
        if os.path.exists(files[0]):
            disassemble_file(file, sys.stdout, native)
        else:
            print("Can't read %s - skipping" % files[0],
                  file=sys.stderr)
            pass
        pass
    return

if __name__ == '__main__':
    main()
