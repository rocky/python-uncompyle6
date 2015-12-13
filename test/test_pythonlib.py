#!/usr/bin/env python
# emacs-mode: -*-python-*-

from __future__ import print_function

'''
test_pythonlib.py -- uncompyle and verify Python libraries

Usage-Examples:

  test_pythonlib.py --all		# decompile all tests (suite + libs)
  test_pythonlib.py --all --verify	# decomyile all tests and verify results
  test_pythonlib.py --test		# decompile only the testsuite
  test_pythonlib.py --2.2 --verify	# decompile and verify python lib 2.2

Adding own test-trees:

Step 1) Edit this file and add a new entry to 'test_options', eg.
  test_options['mylib'] = ('/usr/lib/mylib', PYOC, 'mylib')
Step 2: Run the test:
  test_pythonlib.py --mylib	  # decompile 'mylib'
  test_pythonlib.py --mylib --verify # decompile verify 'mylib'
'''

import getopt, os, py_compile, sys, shutil, tempfile, time

from uncompyle6 import main, verify
from fnmatch import fnmatch

def get_srcdir():
    filename = os.path.normcase(os.path.dirname(__file__))
    return os.path.realpath(filename)

src_dir = get_srcdir()

#----- configure this for your needs

lib_prefix = [src_dir, '/usr/lib/', '/usr/local/lib/']

target_base = tempfile.mkdtemp(prefix='py-dis-')

PY = ('*.py', )
PYC = ('*.pyc', )
PYO = ('*.pyo', )
PYOC = ('*.pyc', '*.pyo')

test_options = {
    # name:   (src_basedir, pattern, output_base_suffix)
    'test':   ['test', PYC, 'test'],
    '2.7':    ['python2.7', PYC, 'python2.7'],
    'ok-2.7': [os.path.join(src_dir, 'ok_2.7'),
               PYC, 'ok-2.7'],
    'base2':  [os.path.join(src_dir, 'base-tests', 'python2'),
               PYC, 'base2'],
}

#-----

def help():
    print("""
Usage-Examples:
  test_pythonlib.py --base2 --verify --compile   # compile, decompyle and verify short tests
  test_pythonlib.py --ok-2.7 --verify            # decompile and verify known good python 2.7
  test_pythonlib.py --2.7             # decompile Python's installed lib files
""")
    sys.exit(1)


def do_tests(src_dir, obj_patterns, target_dir, opts):

    def file_matches(files, root, basenames, patterns):
        files.extend(
            [os.path.normpath(os.path.join(root, n))
                 for n in basenames
                    for pat in patterns
                        if fnmatch(n, pat)])

    files = []
    if opts['do_compile']:
        for root, dirs, basenames in os.walk(src_dir):
            file_matches(files, root, basenames, PY)
            for sfile in files:
                py_compile.compile(sfile)
                pass
            pass
        files = []

    for root, dirs, basenames in os.walk(src_dir):
        file_matches(files, root, basenames, obj_patterns)

    if not files:
        print("Didn't come up with any files to test! Try with --compile?",
              file=sys.stderr)
        exit(1)

    files.sort()

    if opts['start_with']:
        try:
            start_with = files.index(start_with)
            files = files[start_with:]
            print('>>> starting with file', files[0])
        except ValueError:
            pass

    print(time.ctime())
    print('Source directory: ', src_dir)
    print('Output directory: ', target_dir)
    try:
        main(src_dir, target_dir, files, [], do_verify=opts['do_verify'])
    except (KeyboardInterrupt, OSError):
        print()
        exit(1)

if __name__ == '__main__':
    test_dirs = []
    checked_dirs = []
    start_with = None

    test_options_keys = list(test_options.keys())
    test_options_keys.sort()
    opts, args = getopt.getopt(sys.argv[1:], '',
                               ['start-with=', 'verify', 'all', 'compile'] \
                               + test_options_keys )
    if not opts: help()

    test_opts = {
        'do_compile': False,
        'do_verify': False,
        'start_with': None,
        }

    for opt, val in opts:
        if opt == '--verify':
            test_opts['do_verify'] = True
        elif opt == '--compile':
            test_opts['do_compile'] = True
        elif opt == '--start-with':
            test_opts['start_with'] = val
        elif opt[2:] in test_options_keys:
            test_dirs.append(test_options[opt[2:]])
        elif opt == '--all':
            for val in test_options_keys:
                test_dirs.append(test_options[val])
        else:
            help()
            pass
        pass

    for src_dir, pattern, target_dir in test_dirs:
        if os.path.isdir(src_dir):
            checked_dirs.append([src_dir, pattern, target_dir])
        else:
            print("Can't find directory %s. Skipping" % src_dir,
                  file=sys.stderr)
            pass
        pass

    if not checked_dirs:
        print("No directories found to check", file=sys.stderr)
        sys.exit(1)

    for src_dir, pattern, target_dir in checked_dirs:
        target_dir = os.path.join(target_base, target_dir)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir, ignore_errors=1)
        do_tests(src_dir, pattern, target_dir, test_opts)
