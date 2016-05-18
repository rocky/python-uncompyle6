#!/usr/bin/env python
# emacs-mode: -*-python-*-
"""
test_pyenvlib -- uncompyle and verify Python libraries

Usage-Examples:

  test_pyenvlib.py --all		# decompile all tests (suite + libs)
  test_pyenvlib.py --all --verify	# decomyile all tests and verify results
  test_pyenvlib.py --test		# decompile only the testsuite
  test_pyenvlib.py --2.7.11 --verify	# decompile and verify python lib 2.7.11

Adding own test-trees:

Step 1) Edit this file and add a new entry to 'test_options', eg.
          test_options['mylib'] = ('/usr/lib/mylib', PYOC, 'mylib')
Step 2: Run the test:
	  test_pyenvlib --mylib	  # decompile 'mylib'
	  test_pyenvlib --mylib --verify # decompile verify 'mylib'
"""

from __future__ import print_function

from uncompyle6 import main, verify, PYTHON3
import os, time, shutil
from fnmatch import fnmatch
import glob

#----- configure this for your needs

target_base = '/tmp/py-dis/'
lib_prefix = os.path.join(os.environ['HOME'], '.pyenv/versions')

PYC = ('*.pyc', )
PYO = ('*.pyo', )
PYOC = ('*.pyc', '*.pyo')

test_options = {
    # name: (src_basedir, pattern, output_base_suffix)
    'test': ('./test', PYOC, 'test'),
    '1.5': (os.path.join(lib_prefix, 'python1.5'), PYC, 'python-lib1.5'),
    '1.6': (os.path.join(lib_prefix, 'python1.6'), PYC, 'python-lib1.6'),
    '2.0': (os.path.join(lib_prefix, 'python2.0'), PYC, 'python-lib2.0'),
    '2.1': (os.path.join(lib_prefix, 'python2.1'), PYC, 'python-lib2.1'),
    '2.2': (os.path.join(lib_prefix, 'python2.2'), PYC, 'python-lib2.2'),
    '2.5': (os.path.join(lib_prefix, 'python2.5'), PYC, 'python-lib2.5'),
    '2.6.9': (os.path.join(lib_prefix, '2.6.9', 'lib', 'python2.6'), PYC, 'python-lib2.6'),
    '2.7.10': (os.path.join(lib_prefix, '2.7.10', 'lib', 'python2.7'), PYC, 'python-lib2.7'),
    '2.7.11': (os.path.join(lib_prefix, '2.7.11', 'lib', 'python2.7'), PYC, 'python-lib2.7'),
    '3.2.6': (os.path.join(lib_prefix, '3.2.6', 'lib', 'python3.2'), PYC, 'python-lib3.2'),
    '3.3.5': (os.path.join(lib_prefix, '3.3.5', 'lib', 'python3.3'), PYC, 'python-lib3.3'),
    '3.4.2': (os.path.join(lib_prefix, '3.4.2', 'lib', 'python3.4'), PYC, 'python-lib3.4')
    }

#-----

def do_tests(src_dir, patterns, target_dir, start_with=None, do_verify=False):

    def visitor(files, dirname, names):
        files.extend(
            [os.path.normpath(os.path.join(dirname, n))
                 for n in names
                    for pat in patterns
                        if fnmatch(n, pat)])

    files = []
    cwd = os.getcwd()
    os.chdir(src_dir)
    if PYTHON3:
        for root, dirname, names in os.walk(os.curdir):
            files.extend(
                [os.path.normpath(os.path.join(root, n))
                     for n in names
                        for pat in patterns
                            if fnmatch(n, pat)])
            pass
        pass
    else:
        os.path.walk(os.curdir, visitor, files)
    os.chdir(cwd)
    files.sort()

    if start_with:
        try:
            start_with = files.index(start_with)
            files = files[start_with:]
            print('>>> starting with file', files[0])
        except ValueError:
            pass

    if len(files) > 200:
        files = [file for file in files if not 'site-packages' in file]
        files = [file for file in files if not 'test' in file]
        if len(files) > 200:
            files = files[:200]

    print(time.ctime())
    main.main(src_dir, target_dir, files, [], do_verify=do_verify)
    print(time.ctime())

if __name__ == '__main__':
    import getopt, sys

    do_verify = 0
    test_dirs = []
    start_with = None

    test_options_keys = list(test_options.keys())
    test_options_keys.sort()
    opts, args = getopt.getopt(sys.argv[1:], '',
                               ['start-with=', 'verify', 'all', ] \
                               + test_options_keys )
    for opt, val in opts:
        if opt == '--verify':
            do_verify = 1
        elif opt == '--start-with':
            start_with = val
        elif opt[2:] in test_options_keys:
            test_dirs.append(test_options[opt[2:]])
        elif opt == '--all':
            for val in test_options_keys:
                test_dirs.append(test_options[val])

    for src_dir, pattern, target_dir in test_dirs:
        if os.path.exists(src_dir):
            target_dir = os.path.join(target_base, target_dir)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir, ignore_errors=1)
            do_tests(src_dir, pattern, target_dir, start_with, do_verify)
        else:
            print("### Path %s doesn't exist; skipping" % src_dir)

# python 1.5:

# test/re_tests		memory error
# test/test_b1		memory error

# Verification notes:
# - xdrlib fails verification due the same lambda used twice
#   (verification is successfull when using original .pyo as
#   input)
#
