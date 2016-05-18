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

import os, sys
from collections import deque

import uncompyle6
from uncompyle6.code import iscode
from uncompyle6.load import check_object_path, load_module
from uncompyle6.scanner import get_scanner

def disco(version, co, out=None, use_uncompyle6_format=False):
    """
    diassembles and deparses a given code block 'co'
    """

    assert iscode(co)

    # store final output stream for case of error
    real_out = out or sys.stdout
    print('# Python %s' % version, file=real_out)
    if co.co_filename:
        print('# Embedded file name: %s' % co.co_filename,
              file=real_out)

    scanner = get_scanner(version)

    disasm = scanner.disassemble_native \
      if (not use_uncompyle6_format) and hasattr(scanner, 'disassemble_native') \
      else scanner.disassemble

    queue = deque([co])
    disco_loop(disasm, queue, real_out, use_uncompyle6_format)


def disco_loop(disasm, queue, real_out, use_uncompyle6_format):
    while len(queue) > 0:
        co = queue.popleft()
        if co.co_name != '<module>':
            print('\n# %s line %d of %s' %
                      (co.co_name, co.co_firstlineno, co.co_filename),
                      file=real_out)
        tokens, customize = disasm(co, use_uncompyle6_format)
        for t in tokens:
            if iscode(t.pattr):
                queue.append(t.pattr)
            print(t.format(), file=real_out)
            pass
        pass

def disassemble_file(filename, outstream=None, native=False):
    """
    disassemble Python byte-code file (.pyc)

    If given a Python source file (".py") file, we'll
    try to find the corresponding compiled object.
    """
    filename = check_object_path(filename)
    version, timestamp, magic_int, co = load_module(filename)
    if type(co) == list:
        for con in co:
            disco(version, con, outstream, native)
    else:
        disco(version, co, outstream, native)
    co = None

def disassemble_files(in_base, out_base, files, outfile=None,
                      native=False):
    """
    in_base	base directory for input files
    out_base	base directory for output files (ignored when
    files	list of filenames to be uncompyled (relative to src_base)
    outfile	write output to this filename (overwrites out_base)

    For redirecting output to
    - <filename>		outfile=<filename> (out_base is ignored)
    - files below out_base	out_base=...
    - stdout			out_base=None, outfile=None
    """
    def _get_outstream(outfile):
        dir = os.path.dirname(outfile)
        failed_file = outfile + '_failed'
        if os.path.exists(failed_file):
            os.remove(failed_file)
        try:
            os.makedirs(dir)
        except OSError:
            pass
        return open(outfile, 'w')

    of = outfile
    if outfile == '-':
        outfile = None # use stdout
    elif outfile and os.path.isdir(outfile):
        out_base = outfile; outfile = None
    elif outfile:
        out_base = outfile; outfile = None

    for filename in files:
        infile = os.path.join(in_base, filename)
        # print (infile, file=sys.stderr)

        if of: # outfile was given as parameter
            outstream = _get_outstream(outfile)
        elif out_base is None:
            outstream = sys.stdout
        else:
            outfile = os.path.join(out_base, filename) + '_dis'
            outstream = _get_outstream(outfile)
            # print(outfile, file=sys.stderr)
            pass

        # try to disassemble the input file
        try:
            disassemble_file(infile, outstream, native)
        except KeyboardInterrupt:
            if outfile:
                outstream.close()
                os.remove(outfile)
            raise
        except:
            if outfile:
                outstream.close()
                os.rename(outfile, outfile + '_failed')
            else:
                sys.stderr.write("\n# Can't disassemble %s\n" % infile)
                import traceback
                traceback.print_exc()
        else: # uncompyle successfull
            if outfile:
                outstream.close()
            if not outfile: print('\n# okay disassembling', infile)
            sys.stdout.flush()

        if outfile:
            sys.stdout.write("\n")
            sys.stdout.flush()
        return

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
