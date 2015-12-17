from __future__ import print_function


'''
  Copyright (c) 1999 John Aycock
  Copyright (c) 2000 by hartmut Goebel <h.goebel@crazy-compilers.com>
  Copyright (c) 2015 by Rocky Bernstein

  Permission is hereby granted, free of charge, to any person obtaining
  a copy of this software and associated documentation files (the
  "Software"), to deal in the Software without restriction, including
  without limitation the rights to use, copy, modify, merge, publish,
  distribute, sublicense, and/or sell copies of the Software, and to
  permit persons to whom the Software is furnished to do so, subject to
  the following conditions:

  The above copyright notice and this permission notice shall be
  included in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

  See the file 'CHANGES' for a list of changes

  NB. This is not a masterpiece of software, but became more like a hack.
  Probably a complete rewrite would be sensefull. hG/2000-12-27
'''

import os, marshal, sys, types

PYTHON_VERSION = sys.version_info.major + (sys.version_info.minor / 10.0)
PYTHON3 = (sys.version_info >= (3, 0))

import uncompyle6
from uncompyle6.scanner import get_scanner
from uncompyle6.disas import check_object_path
import uncompyle6.marsh
from uncompyle6 import walker, verify, magics

sys.setrecursionlimit(5000)
__all__ = ['uncompyle_file', 'main']

def _load_file(filename):
    '''
    load a Python source file and compile it to byte-code
    _load_file(filename: string): code_object
    filename:	name of file containing Python source code
                (normally a .py)
    code_object: code_object compiled from this source code
    This function does NOT write any file!
    '''
    fp = open(filename, 'rb')
    source = fp.read().decode('utf-8') + '\n'
    try:
        co = compile(source, filename, 'exec', dont_inherit=True)
    except SyntaxError:
        print('>>Syntax error in %s\n' % filename, file= sys.stderr)
        raise
    fp.close()
    return co

def load_module(filename):
    '''
    load a module without importing it
    load_module(filename: string): code_object
    filename:	name of file containing Python byte-code object
                (normally a .pyc)
    code_object: code_object from this file
    '''

    with open(filename, 'rb') as fp:
        magic = fp.read(4)
        try:
            version = float(magics.versions[magic])
        except KeyError:
            raise ImportError("Unknown magic number %s in %s" %
                              (ord(magic[0])+256*ord(magic[1]), filename))
        if not (2.5 <= version <= 2.7) and not (3.2 <= version <= 3.4):
            raise ImportError("This is a Python %s file! Only "
                              "Python 2.5 to 2.7 and 3.2 to 3.4 files are supported."
                              % version)

        # print version
        fp.read(4) # timestamp
        magic_int = magics.magic2int(magic)

        if version == PYTHON_VERSION:
            # Note: a higher magic number necessarily mean a later
            # release.  At Python 3.0 the magic number decreased
            # significantly. Hence the range below. Also note
            # inclusion of the size info, occurred within a
            # Python magor/minor release. Hence the test on the
            # magic value rather than PYTHON_VERSION
            if 3200 <= magic_int < 20121:
                fp.read(4) # size mod 2**32
            bytecode = fp.read()
            co = marshal.loads(bytecode)
        else:
            co = uncompyle6.marsh.load_code(fp, magic_int)
        pass

    return version, co

def uncompyle(version, co, out=None, showasm=False, showast=False):
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

    scanner = get_scanner(version)
    tokens, customize = scanner.disassemble(co)

    if showasm:
        for t in tokens:
            print(t, file=real_out)
        print(file=out)

    #  Build AST from disassembly.
    walk = walker.Walker(version, out, scanner, showast=showast)
    try:
        ast = walk.build_ast(tokens, customize)
    except walker.ParserError as e :  # parser failed, dump disassembly
        print(e, file=real_out)
        raise
    del tokens # save memory

    # convert leading '__doc__ = "..." into doc string
    assert ast == 'stmts'
    try:
        if ast[0][0] == walker.ASSIGN_DOC_STRING(co.co_consts[0]):
            walk.print_docstring('', co.co_consts[0])
            del ast[0]
        if ast[-1] == walker.RETURN_NONE:
            ast.pop() # remove last node
            # todo: if empty, add 'pass'
    except:
        pass
    walk.mod_globs = walker.find_globals(ast, set())
    walk.gen_source(ast, customize)
    for g in walk.mod_globs:
        walk.write('global %s ## Warning: Unused global' % g)
    if walk.ERROR:
        raise walk.ERROR

def uncompyle_file(filename, outstream=None, showasm=False, showast=False):
    """
    decompile Python byte-code file (.pyc)
    """
    check_object_path(filename)
    version, co = load_module(filename)
    if type(co) == list:
        for con in co:
            uncompyle(version, con, outstream, showasm, showast)
    else:
        uncompyle(version, co, outstream, showasm, showast)
    co = None

# ---- main ----

if sys.platform.startswith('linux') and os.uname()[2][:2] in ['2.', '3.', '4.']:
    def __memUsage():
        mi = open('/proc/self/stat', 'r')
        from trepan.api import debug; debug()
        mu = mi.readline().split()[22]
        mi.close()
        return int(mu) / 1000000
else:
    def __memUsage():
        return ''

def status_msg(do_verify, tot_files, okay_files, failed_files,
               verify_failed_files):
    if tot_files == 1:
        if failed_files:
            return "decompile failed"
        elif verify_failed_files:
            return "decompile verify failed"
        else:
            return "Successfully decompiled file"
            pass
        pass
    mess = "decompiled %i files: %i okay, %i failed" % (tot_files, okay_files, failed_files)
    if do_verify:
        mess += (", %i verify failed" % verify_failed_files)
    return mess


def main(in_base, out_base, files, codes, outfile=None,
         showasm=False, showast=False, do_verify=False):
    '''
    in_base	base directory for input files
    out_base	base directory for output files (ignored when
    files	list of filenames to be uncompyled (relative to src_base)
    outfile	write output to this filename (overwrites out_base)

    For redirecting output to
    - <filename>		outfile=<filename> (out_base is ignored)
    - files below out_base	out_base=...
    - stdout			out_base=None, outfile=None
    '''
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
    tot_files = okay_files = failed_files = verify_failed_files = 0

    # for code in codes:
    #    version = sys.version[:3] # "2.5"
    #    with open(code, "r") as f:
    #        co = compile(f.read(), "", "exec")
    #    uncompyle(sys.version[:3], co, sys.stdout, showasm=showasm, showast=showast)

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

        # try to decomyple the input file
        try:
            uncompyle_file(infile, outstream, showasm, showast)
            tot_files += 1
        except ValueError as e:
            sys.stderr.write("\n# %s" % e)
            failed_files += 1
        except KeyboardInterrupt:
            if outfile:
                outstream.close()
                os.remove(outfile)
            sys.stderr.write("\nLast file: %s   " % (infile))
            raise
        except:
            failed_files += 1
            if outfile:
                outstream.close()
                os.rename(outfile, outfile + '_failed')
            else:
                sys.stderr.write("\n# Can't uncompyle %s\n" % infile)
        else: # uncompyle successfull
            if outfile:
                outstream.close()
            if do_verify:
                try:
                    verify.compare_code_with_srcfile(infile, outfile)
                    if not outfile: print('\n# okay decompyling', infile, __memUsage())
                    okay_files += 1
                except verify.VerifyCmpError as e:
                    verify_failed_files += 1
                    os.rename(outfile, outfile + '_unverified')
                    if not outfile:
                        print("### Error Verifiying %s" % filename,  file=sys.stderr)
                        print(e, file=sys.stderr)
            else:
                okay_files += 1
                if not outfile:
                    mess = '\n# okay decompyling'
                    # mem_usage = __memUsage()
                    print(mess, infile)
        if outfile:
            sys.stdout.write("%s\r" %
                             status_msg(do_verify, tot_files, okay_files, failed_files, verify_failed_files))
            sys.stdout.flush()
    if outfile:
        sys.stdout.write("\n")
        sys.stdout.flush()
    return (tot_files, okay_files, failed_files, verify_failed_files)
