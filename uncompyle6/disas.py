"""
CPython magic- and version- independent disassembly routines

Copyright (c) 1999 John Aycock
Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
Copyright (c) 2015 by Rocky Bernstein

This is needed when the bytecode extracted is from
a different version than the currently-running Python.

When the two are the same, you can simply use Python's built-in disassemble
"""

from __future__ import print_function

import os, sys, types

import uncompyle6

def disco(version, co, out=None):
    """
    diassembles and deparses a given code block 'co'
    """

    assert isinstance(co, types.CodeType)

    # store final output stream for case of error
    real_out = out or sys.stdout
    print('# Python %s' % version, file=real_out)
    if co.co_filename:
        print('# Embedded file name: %s' % co.co_filename,
              file=real_out)

    # Pick up appropriate scanner
    if version == 2.7:
        import uncompyle6.scanners.scanner27 as scan
        scanner = scan.Scanner27()
    elif version == 2.6:
        import uncompyle6.scanners.scanner26 as scan
        scanner = scan.Scanner26()
    elif version == 2.5:
        import uncompyle6.scanners.scanner25 as scan
        scanner = scan.Scanner25()
    elif version == 3.2:
        import uncompyle6.scanners.scanner32 as scan
        scanner = scan.Scanner32()
    elif version == 3.4:
        import uncompyle6.scanners.scanner34 as scan
        scanner = scan.Scanner34()
    scanner.setShowAsm(True, out)
    tokens, customize = scanner.disassemble(co)

    for t in tokens:
        print(t, file=real_out)
    print(file=out)


def disassemble_file(filename, outstream=None):
    """
    disassemble Python byte-code file (.pyc)
    """
    version, co = uncompyle6.load_module(filename)
    if type(co) == list:
        for con in co:
            disco(version, con, outstream)
    else:
        disco(version, co, outstream)
    co = None

def disassemble_files(in_base, out_base, files, outfile=None):
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

        # try to decomyple the input file
        try:
            disassemble_file(infile, outstream)
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
            if not outfile: print('\n# okay decompyling', infile)
            sys.stdout.flush()

        if outfile:
            sys.stdout.write("\n")
            sys.stdout.flush()
        return

def _test():
    """Simple test program to disassemble a file."""
    argc = len(sys.argv)
    if argc != 2:
        sys.stderr.write("usage: %s [-|CPython compiled file]\n" % __file__)
        sys.exit(2)
    fn = sys.argv[1]
    disassemble_file(fn)

if __name__ == "__main__":
    _test()
