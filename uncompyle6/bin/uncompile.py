#!/usr/bin/env python
# Mode: -*- python -*-
#
# Copyright (c) 2015-2017, 2019-2020 by Rocky Bernstein
# Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#
import sys, os, getopt, time
from xdis.version_info import version_tuple_to_str

program = 'uncompyle6'

__doc__ = """
Usage:
  %s [OPTIONS]... [ FILE | DIR]...
  %s [--help | -h | --V | --version]

Examples:
  %s      foo.pyc bar.pyc       # decompile foo.pyc, bar.pyc to stdout
  %s -o . foo.pyc bar.pyc       # decompile to ./foo.pyc_dis and ./bar.pyc_dis
  %s -o /tmp /usr/lib/python1.5 # decompile whole library

Options:
  -o <path>     output decompiled files to this path:
                if multiple input files are decompiled, the common prefix
                is stripped from these names and the remainder appended to
                <path>
                  uncompyle6 -o /tmp bla/fasel.pyc bla/foo.pyc
                    -> /tmp/fasel.pyc_dis, /tmp/foo.pyc_dis
                  uncompyle6 -o /tmp bla/fasel.pyc bar/foo.pyc
                    -> /tmp/bla/fasel.pyc_dis, /tmp/bar/foo.pyc_dis
                  uncompyle6 -o /tmp /usr/lib/python1.5
                    -> /tmp/smtplib.pyc_dis ... /tmp/lib-tk/FixTk.pyc_dis
  --compile | -c <python-file>
                attempts a decompilation after compiling <python-file>
  -d            print timestamps
  -p <integer>  use <integer> number of processes
  -r            recurse directories looking for .pyc and .pyo files
  --fragments   use fragments deparser
  --verify      compare generated source with input byte-code
  --verify-run  compile generated source, run it and check exit code
  --syntax-verify compile generated source
  --linemaps    generated line number correspondencies between byte-code
                and generated source output
  --encoding  <encoding>
                use <encoding> in generated source according to pep-0263
  --help        show this message

Debugging Options:
  --asm     | -a        include byte-code       (disables --verify)
  --grammar | -g        show matching grammar
  --tree={before|after}
  -t {before|after}     include syntax before (or after) tree transformation
                        (disables --verify)
  --tree++ | -T         add template rules to --tree=before when possible

Extensions of generated files:
  '.pyc_dis' '.pyo_dis'   successfully decompiled (and verified if --verify)
    + '_unverified'       successfully decompile but --verify failed
    + '_failed'           decompile failed (contact author for enhancement)
""" % ((program,) * 5)

program = 'uncompyle6'

from uncompyle6 import verify
from uncompyle6.main import main, status_msg
from uncompyle6.version import __version__

def usage():
    print(__doc__)
    sys.exit(1)


def main_bin():
    if not (sys.version_info[0:2] in ((2, 4), (2, 5), (2, 6), (2, 7), (3, 0),
                                      (3, 1), (3, 2), (3, 3),
                                      (3, 4), (3, 5), (3, 6),
                                      (3, 7), (3, 8), (3, 9), (3, 10)
        )):
        print('Error: %s requires Python 2.4-3.10' % program)
        sys.exit(-1)

    do_verify = recurse_dirs = False
    numproc = 0
    outfile = '-'
    out_base = None
    source_paths = []
    timestamp = False
    timestampfmt = "# %Y.%m.%d %H:%M:%S %Z"

    try:
        opts, pyc_paths = getopt.getopt(sys.argv[1:], 'hac:gtTdrVo:p:',
                                    'help asm compile= grammar linemaps recurse '
                                    'timestamp tree= tree+ '
                                    'fragments verify verify-run version '
                                    'syntax-verify '
                                    'showgrammar encoding='.split(' '))
    except getopt.GetoptError, e:
        sys.stderr.write('%s: %s\n' %
                         (os.path.basename(sys.argv[0]), e))
        sys.exit(-1)

    options = {}
    for opt, val in opts:
        if opt in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)
        elif opt in ('-V', '--version'):
            print("%s %s" % (program, __version__))
            sys.exit(0)
        elif opt == '--verify':
            options['do_verify'] = 'strong'
        elif opt == '--syntax-verify':
            options['do_verify'] = 'weak'
        elif opt == '--fragments':
            options['do_fragments'] = True
        elif opt == '--verify-run':
            options['do_verify'] = 'verify-run'
        elif opt == '--linemaps':
            options['do_linemaps'] = True
        elif opt in ('--asm', '-a'):
            options['showasm'] = 'after'
            options['do_verify'] = None
        elif opt in ('--tree', '-t'):
            if 'showast' not in options:
                options['showast'] = {}
            if val == 'before':
                options['showast'][val] = True
            elif val == 'after':
                options['showast'][val] = True
            else:
                options['showast']['before'] = True
            options['do_verify'] = None
        elif opt in ('--tree+', '-T'):
            if 'showast' not in options:
                options['showast'] = {}
            options['showast']['after'] = True
            options['showast']['before'] = True
            options['do_verify'] = None
        elif opt in ('--grammar', '-g'):
            options['showgrammar'] = True
        elif opt == '-o':
            outfile = val
        elif opt in ('--timestamp', '-d'):
            timestamp = True
        elif opt in ('--compile', '-c'):
            source_paths.append(val)
        elif opt == '-p':
            numproc = int(val)
        elif opt in ('--recurse', '-r'):
            recurse_dirs = True
        elif opt == '--encoding':
            options['source_encoding'] = val
        else:
            sys.stderr.write(opt)
            usage()

    # expand directory if specified
    if recurse_dirs:
        expanded_files = []
        for f in pyc_paths:
            if os.path.isdir(f):
                for root, _, dir_files in os.walk(f):
                    for df in dir_files:
                        if df.endswith('.pyc') or df.endswith('.pyo'):
                            expanded_files.append(os.path.join(root, df))
        pyc_paths = expanded_files

    # argl, commonprefix works on strings, not on path parts,
    # thus we must handle the case with files in 'some/classes'
    # and 'some/cmds'
    src_base = os.path.commonprefix(pyc_paths)
    if src_base[-1:] != os.sep:
        src_base = os.path.dirname(src_base)
    if src_base:
        sb_len = len( os.path.join(src_base, '') )
        pyc_paths = [f[sb_len:] for f in pyc_paths]

    if not pyc_paths:
        sys.stderr.write("No files given\n")
        usage()

    if outfile == '-':
        outfile = None # use stdout
    elif outfile and os.path.isdir(outfile):
        out_base = outfile; outfile = None
    elif outfile and len(pyc_paths) > 1:
        out_base = outfile; outfile = None

    if timestamp:
        print(time.strftime(timestampfmt))

    if numproc <= 1:
        try:
            result = main(src_base, out_base, pyc_paths, source_paths, outfile,
                          **options)
            result = [options.get('do_verify', None)] + list(result)
            if len(pyc_paths) > 1:
                mess = status_msg(*result)
                print('# ' + mess)
                pass
        except ImportError:
            print(str(sys.exc_info()[1]))
            sys.exit(2)
        except (KeyboardInterrupt):
            pass
        except verify.VerifyCmpError:
            raise
    else:
        from multiprocessing import Process, Queue

        try:
            from Queue import Empty
        except ImportError:
            from queue import Empty

        fqueue = Queue(len(pyc_paths)+numproc)
        for f in pyc_paths:
            fqueue.put(f)
        for i in range(numproc):
            fqueue.put(None)

        rqueue = Queue(numproc)

        def process_func():
            try:
                (tot_files, okay_files, failed_files, verify_failed_files) = (0, 0, 0, 0)
                while 1:
                    f = fqueue.get()
                    if f is None:
                        break
                    (t, o, f, v) = \
                      main(src_base, out_base, [f], [], outfile, **options)
                    tot_files += t
                    okay_files += o
                    failed_files += f
                    verify_failed_files += v
            except (Empty, KeyboardInterrupt):
                pass
            rqueue.put((tot_files, okay_files, failed_files, verify_failed_files))
            rqueue.close()

        try:
            procs = [Process(target=process_func) for i in range(numproc)]
            for p in procs:
                p.start()
            for p in procs:
                p.join()
            try:
                (tot_files, okay_files, failed_files, verify_failed_files) = (0, 0, 0, 0)
                while True:
                    (t, o, f, v) = rqueue.get(False)
                    tot_files += t
                    okay_files += o
                    failed_files += f
                    verify_failed_files += v
            except Empty:
                pass
            print('# decompiled %i files: %i okay, %i failed, %i verify failed' %
                  (tot_files, okay_files, failed_files, verify_failed_files))
        except (KeyboardInterrupt, OSError):
            pass

    if timestamp:
        print(time.strftime(timestampfmt))

    return

if __name__ == '__main__':
    main_bin()
