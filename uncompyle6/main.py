import datetime, os, subprocess, sys, tempfile

from uncompyle6 import verify, IS_PYPY
from xdis.code import iscode
from uncompyle6.disas import check_object_path
from uncompyle6.semantics import pysource
from uncompyle6.parser import ParserError
from uncompyle6.version import VERSION
from uncompyle6.linenumbers import line_number_mapping

from xdis.load import load_module

def uncompyle(
        bytecode_version, co, out=None, showasm=None, showast=False,
        timestamp=None, showgrammar=False, code_objects={},
        source_size=None, is_pypy=False, magic_int=None):
    """
    ingests and deparses a given code block 'co'
    """
    assert iscode(co)

    # store final output stream for case of error
    real_out = out or sys.stdout
    if is_pypy:
        co_pypy_str = 'PyPy '
    else:
        co_pypy_str = ''

    if IS_PYPY:
        run_pypy_str = 'PyPy '
    else:
        run_pypy_str = ''

    if magic_int:
        m = str(magic_int)
    else:
        m = ""
    real_out.write('# uncompyle6 version %s\n'
          '# %sPython bytecode %s%s\n# Decompiled from: %sPython %s\n' %
          (VERSION, co_pypy_str, bytecode_version,
           " (%s)" % m, run_pypy_str,
           '\n# '.join(sys.version.split('\n'))))
    if co.co_filename:
        real_out.write('# Embedded file name: %s\n' % co.co_filename)
    if timestamp:
        real_out.write('# Compiled at: %s\n' %
                       datetime.datetime.fromtimestamp(timestamp))
    if source_size:
        real_out.write('# Size of source mod 2**32: %d bytes\n' % source_size)

    pysource.deparse_code(bytecode_version, co, out, showasm, showast,
                          showgrammar, code_objects=code_objects,
                          is_pypy=is_pypy)


def uncompyle_file(filename, outstream=None, showasm=None, showast=False,
                   showgrammar=False):
    """
    decompile Python byte-code file (.pyc)
    """

    filename = check_object_path(filename)
    code_objects = {}
    (version, timestamp, magic_int, co, is_pypy,
     source_size) = load_module(filename, code_objects)

    if type(co) == list:
        for con in co:
            uncompyle(version, con, outstream, showasm, showast,
                      timestamp, showgrammar, code_objects=code_objects,
                      is_pypy=is_pypy, magic_int=magic_int)
    else:
        uncompyle(version, co, outstream, showasm, showast,
                  timestamp, showgrammar,
                  code_objects=code_objects, source_size=source_size,
                  is_pypy=is_pypy, magic_int=magic_int)
    co = None

# FIXME: combine into an options parameter
def main(in_base, out_base, files, codes, outfile=None,
         showasm=None, showast=False, do_verify=False,
         showgrammar=False, raise_on_error=False,
         do_linemaps=False):
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

    tot_files = okay_files = failed_files = verify_failed_files = 0

    # for code in codes:
    #    version = sys.version[:3] # "2.5"
    #    with open(code, "r") as f:
    #        co = compile(f.read(), "", "exec")
    #    uncompyle(sys.version[:3], co, sys.stdout, showasm=showasm, showast=showast)

    for filename in files:
        infile = os.path.join(in_base, filename)
        if not os.path.exists(infile):
            sys.stderr.write("File '%s' doesn't exist. Skipped\n"
                             % infile)
            continue

        # print (infile, file=sys.stderr)

        if outfile: # outfile was given as parameter
            outstream = _get_outstream(outfile)
        elif out_base is None:
            outstream = sys.stdout
            if do_linemaps or do_verify:
                prefix = os.path.basename(filename)
                if prefix.endswith('.py'):
                    prefix = prefix[:-len('.py')]
                junk, outfile = tempfile.mkstemp(suffix=".py",
                                             prefix=prefix)
                # Unbuffer output if possible
                if sys.stdout.isatty():
                    buffering = -1
                else:
                    buffering = 0
                sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering)
                tee = subprocess.Popen(["tee", outfile], stdin=subprocess.PIPE)
                os.dup2(tee.stdin.fileno(), sys.stdout.fileno())
                os.dup2(tee.stdin.fileno(), sys.stderr.fileno())
        else:
            if filename.endswith('.pyc'):
                outfile = os.path.join(out_base, filename[0:-1])
            else:
                outfile = os.path.join(out_base, filename) + '_dis'
            outstream = _get_outstream(outfile)
        # print(outfile, file=sys.stderr)

        # Try to uncompile the input file
        try:
            uncompyle_file(infile, outstream, showasm, showast, showgrammar)
            tot_files += 1
        except (ValueError, SyntaxError, ParserError, pysource.SourceWalkerError):
            sys.stdout.write("\n")
            sys.stderr.write("# file %s\n" % (infile))
            failed_files += 1
        except KeyboardInterrupt:
            if outfile:
                outstream.close()
                os.remove(outfile)
            sys.stdout.write("\n")
            sys.stderr.write("\nLast file: %s   " % (infile))
            raise
        # except:
        #     failed_files += 1
        #     if outfile:
        #         outstream.close()
        #         os.rename(outfile, outfile + '_failed')
        #     else:
        #         sys.stderr.write("\n# %s" % sys.exc_info()[1])
        #         sys.stderr.write("\n# Can't uncompile %s\n" % infile)
        else: # uncompile successful
            if outfile:
                if do_linemaps:
                    mapping = line_number_mapping(infile, outfile)
                    outstream.write("\n\n## Line number correspondences\n")
                    import pprint
                    s = pprint.pformat(mapping, indent=2, width=80)
                    s2 = '##' + '\n##'.join(s.split("\n")) + "\n"
                    outstream.write(s2)
                outstream.close()

                if do_verify:
                    weak_verify = do_verify == 'weak'
                    try:
                        msg = verify.compare_code_with_srcfile(infile, outfile, weak_verify=weak_verify)
                        if not outfile:
                            if not msg:
                                print '\n# okay decompiling %s' % infile
                                okay_files += 1
                            else:
                                print '\n# %s\n\t%s', infile, msg
                    except verify.VerifyCmpError, e:
                        print(e)
                        verify_failed_files += 1
                        os.rename(outfile, outfile + '_unverified')
                        sys.stderr.write("### Error Verifying %s\n" % filename)
                        sys.stderr.write(str(e) + "\n")
                        if not outfile:
                            sys.stder.write("### Error Verifiying %s" %
                                            filename)
                            sys.stderr.write(e)
                            if raise_on_error:
                                raise
                            pass
                        pass
                pass
            elif do_verify:
                sys.stderr.write("\n### uncompile successful, "
                                 "but no file to compare against")
                pass
            else:
                okay_files += 1
                if not outfile:
                    mess = '\n# okay decompiling'
                    # mem_usage = __memUsage()
                    print mess, infile
        if outfile:
            sys.stdout.write("%s\r" %
                             status_msg(do_verify, tot_files, okay_files, failed_files, verify_failed_files))
            sys.stdout.flush()
    if outfile:
        sys.stdout.write("\n")
        sys.stdout.flush()
    return (tot_files, okay_files, failed_files, verify_failed_files)


# ---- main ----

if sys.platform.startswith('linux') and os.uname()[2][:2] in ['2.', '3.', '4.']:
    def __memUsage():
        mi = open('/proc/self/stat', 'r')
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
            return "\n# decompile failed"
        elif verify_failed_files:
            return "\n# decompile verify failed"
        else:
            return "\n# Successfully decompiled file"
            pass
        pass
    mess = "decompiled %i files: %i okay, %i failed" % (tot_files, okay_files, failed_files)
    if do_verify:
        mess += (", %i verify failed" % verify_failed_files)
    return mess
