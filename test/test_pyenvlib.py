#!/usr/bin/env python
# emacs-mode: -*-python-*-
"""
test_pyenvlib -- uncompyle and verify Python libraries

Usage-Examples:

  test_pyenvlib.py --all		# decompile all tests (suite + libs)
  test_pyenvlib.py --all --verify	# decomyile all tests and verify results
  test_pyenvlib.py --test		# decompile only the testsuite
  test_pyenvlib.py --2.7.12 --verify	# decompile and verify python lib 2.7.11

Adding own test-trees:

Step 1) Edit this file and add a new entry to 'test_options', eg.
          test_options['mylib'] = ('/usr/lib/mylib', PYOC, 'mylib')
Step 2: Run the test:
	  test_pyenvlib --mylib	  # decompile 'mylib'
	  test_pyenvlib --mylib --verify # decompile verify 'mylib'
"""

from __future__ import print_function

from uncompyle6 import main, PYTHON3
import os, time, shutil, sys
from fnmatch import fnmatch

#----- configure this for your needs

TEST_VERSIONS=('2.3.7', '2.4.6', '2.5.6', '2.6.9',
               'pypy-2.4.0', 'pypy-2.6.1',
               'pypy-5.0.1', 'pypy-5.3.1',
               '2.7.10', '2.7.11', '2.7.12', '2.7.13',
               '3.0.1', '3.1.5', '3.2.6',
               '3.3.5', '3.3.6',
               '3.4.2', '3.5.1', '3.6.0', 'native')

target_base = '/tmp/py-dis/'
lib_prefix = os.path.join(os.environ['HOME'], '.pyenv/versions')

PYC = ('*.pyc', )
PYO = ('*.pyo', )
PYOC = ('*.pyc', '*.pyo')

#-----

test_options = {
    # name: (src_basedir, pattern, output_base_suffix)
    'test': ('./test', PYOC, 'test'),
    }

for vers in TEST_VERSIONS:
    if vers.startswith('pypy-'):
        short_vers = vers[0:-2]
        test_options[vers] = (os.path.join(lib_prefix, vers, 'lib_pypy'),
                              PYC, 'python-lib'+short_vers)
    if vers == 'native':
        short_vers = os.path.basename(sys.path[-1])
        test_options[vers] = (sys.path[-1],
                              PYC, short_vers)

    else:
        short_vers = vers[:3]
        test_options[vers] = (os.path.join(lib_prefix, vers, 'lib', 'python'+short_vers),
                              PYC, 'python-lib'+short_vers)

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

    do_coverage = do_verify = False
    test_dirs = []
    start_with = None

    test_options_keys = list(test_options.keys())
    test_options_keys.sort()
    opts, args = getopt.getopt(sys.argv[1:], '',
                               ['start-with=', 'verify', 'weak-verify',
                                'coverage', 'all', ] \
                               + test_options_keys )
    vers = ''
    for opt, val in opts:
        if opt == '--verify':
            do_verify = True
        if opt == '--weak-verify':
            do_verify = 'weak'
        if opt == '--coverage':
            do_coverage = True
        elif opt == '--start-with':
            start_with = val
        elif opt[2:] in test_options_keys:
            triple = test_options[opt[2:]]
            vers = triple[-1]
            test_dirs.append(triple)
        elif opt == '--all':
            vers = 'all'
            for val in test_options_keys:
                test_dirs.append(test_options[val])

    if do_coverage:
        os.environ['SPARK_PARSER_COVERAGE'] = (
            '/tmp/spark-grammar-%s.cover' % vers
            )

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
