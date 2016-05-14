#!/usr/bin/env python
# Mode: -*- python -*-
#
# Copyright (c) 2015-2016 by Rocky Bernstein <rb@dustyfeet.com>
#
from __future__ import print_function
import sys, os, getopt

program =  os.path.basename(__file__)

__doc__ = """
Usage:
  %s [OPTIONS]... FILE
  %s [--help | -h | -V | --version]

Examples:
  %s foo.pyc
  %s foo.py
  %s -o foo.pydis foo.pyc
  %s -o /tmp foo.pyc

Options:
  -o <path>     output decompiled files to this path:
                if multiple input files are decompiled, the common prefix
                is stripped from these names and the remainder appended to
                <path>
  --help        show this message

""" % ((program,) * 6)

def main():
    Usage_short = \
    "%s [--help] [--verify] [--showasm] [--showast] [-o <path>] FILE|DIR..." % program

    from uncompyle6 import check_python_version
    from uncompyle6.disas import disassemble_files
    from uncompyle6.version import VERSION

    check_python_version(program)

    outfile = '-'
    out_base = None

    if len(sys.argv) == 1:
        print("No file(s) or directory given", file=sys.stderr)
        print(Usage_short, file=sys.stderr)
        sys.exit(1)

    try:
        opts, files = getopt.getopt(sys.argv[1:], 'hVo:', ['help', 'version'])
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
        elif opt == '-o':
            outfile = val
        else:
            print(opt)
            print(Usage_short, file=sys.stderr)
            sys.exit(1)


    # argl, commonprefix works on strings, not on path parts,
    # thus we must handle the case with files in 'some/classes'
    # and 'some/cmds'
    src_base = os.path.commonprefix(files)
    if src_base[-1:] != os.sep:
        src_base = os.path.dirname(src_base)
    if src_base:
        sb_len = len( os.path.join(src_base, '') )
        files = [f[sb_len:] for f in files]
        del sb_len

    if outfile == '-':
        outfile = None # use stdout
    elif outfile and os.path.isdir(outfile):
        out_base = outfile; outfile = None
    elif outfile and len(files) > 1:
        out_base = outfile; outfile = None

    disassemble_files(src_base, out_base, files, outfile)
    return

if __name__ == '__main__':
    main()
