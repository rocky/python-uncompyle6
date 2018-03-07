#!/usr/bin/env python
# emacs-mode: -*-python-*-
"""
test_pyenvlib -- uncompyle and verify Python libraries

Usage-Examples:

  test_pyenvlib.py --all		# decompile all tests (suite + libs)
  test_pyenvlib.py --all --verify	# decomyile all tests and verify results
  test_pyenvlib.py --test		# decompile only the testsuite
  test_pyenvlib.py --2.7.12 --verify	# decompile and verify python lib 2.7.11
  test_pyenvlib.py --3.6.4 --max 10	# decompile first 10 of 3.6.4

Adding own test-trees:

Step 1) Edit this file and add a new entry to 'test_options', eg.
          test_options['mylib'] = ('/usr/lib/mylib', PYOC, 'mylib')
Step 2: Run the test:
	  test_pyenvlib --mylib	  # decompile 'mylib'
	  test_pyenvlib --mylib --verify # decompile verify 'mylib'
"""

from __future__ import print_function

import os, time, re, shutil, sys
from fnmatch import fnmatch

from uncompyle6 import main, PYTHON3
import xdis.magics as magics

#----- configure this for your needs

python_versions = [v for v in magics.python_versions if
                       re.match('^[0-9.]+$', v)]

# FIXME: we should remove Python versions that we don't support.
# These include Jython, and Python bytecode changes pre release.

TEST_VERSIONS=(
               'pypy-2.4.0', 'pypy-2.6.1',
               'pypy-5.0.1', 'pypy-5.3.1', 'pypy3.5-5.7.1-beta',
               'native') + tuple(python_versions)


target_base = '/tmp/py-dis/'
lib_prefix = os.path.join(os.environ['HOME'], '.pyenv/versions')

PYC = ('*.pyc', )
PYO = ('*.pyo', )
PYOC = ('*.pyc', '*.pyo')

#-----

test_options = {
    # name: (src_basedir, pattern, output_base_suffix)
    'test': ('./test', PYOC, 'test'),
    'max=': 200,
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

def do_tests(src_dir, patterns, target_dir, start_with=None,
             do_verify=False, max_files=200):

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

    if len(files) > max_files:
        files = [file for file in files if not 'site-packages' in file]
        files = [file for file in files if not 'test' in file]
        if len(files) > max_files:
            # print("Numer of files %d - truncating to last 200" % len(files))
            print("Numer of files %d - truncating to first %s" %
                  (len(files), max_files))
            files = files[:max_files]

    print(time.ctime())
    (tot_files, okay_files, failed_files,
     verify_failed_files) = main.main(src_dir, target_dir, files, [], do_verify=do_verify)
    print(time.ctime())
    return verify_failed_files + failed_files

if __name__ == '__main__':
    import getopt, sys

    do_coverage = do_verify = False
    test_dirs = []
    start_with = None

    test_options_keys = list(test_options.keys())
    test_options_keys.sort()
    opts, args = getopt.getopt(sys.argv[1:], '',
                               ['start-with=', 'verify', 'verify-run', 'weak-verify',
                                'max=', 'coverage', 'all', ] \
                               + test_options_keys )
    vers = ''

    for opt, val in opts:
        if opt == '--verify':
            do_verify = 'strong'
        elif opt == '--weak-verify':
            do_verify = 'weak'
        elif opt == '--verify-run':
            do_verify = 'verify-run'
        elif opt == '--coverage':
            do_coverage = True
        elif opt == '--start-with':
            start_with = val
        elif opt[2:] in test_options_keys:
            triple = test_options[opt[2:]]
            vers = triple[-1]
            test_dirs.append(triple)
        elif opt == '--max':
            test_options['max='] = int(val)
        elif opt == '--all':
            vers = 'all'
            for val in test_options_keys:
                test_dirs.append(test_options[val])

    if do_coverage:
        os.environ['SPARK_PARSER_COVERAGE'] = (
            '/tmp/spark-grammar-%s.cover' % vers
            )

    failed = 0
    for src_dir, pattern, target_dir in test_dirs:
        if os.path.exists(src_dir):
            target_dir = os.path.join(target_base, target_dir)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir, ignore_errors=1)
            failed += do_tests(src_dir, pattern, target_dir, start_with,
                               do_verify, test_options['max='])
        else:
            print("### Path %s doesn't exist; skipping" % src_dir)
            pass
        pass
    sys.exit(failed)

# python 1.5:

# test/re_tests		memory error
# test/test_b1		memory error

# Verification notes:
# - xdrlib fails verification due the same lambda used twice
#   (verification is successfull when using original .pyo as
#   input)
#
