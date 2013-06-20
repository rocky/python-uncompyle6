#! python

'''
test_pythonlib -- uncompyle and verify Python libraries

Usage-Examples:

  test_pythonlib --all		# decompile all tests (suite + libs)
  test_pythonlib --all --verify	# decomyile all tests and verify results
  test_pythonlib --test		# decompile only the testsuite
  test_pythonlib --2.2 --verify	# decompile and verify python lib 2.2

Adding own test-trees:

Step 1) Edit this file and add a new entry to 'test_options', eg.
  test_options['mylib'] = ('/usr/lib/mylib', PYOC, 'mylib')
Step 2: Run the test:
  test_pythonlib --mylib	  # decompile 'mylib'
  test_pythonlib --mylib --verify # decompile verify 'mylib'
'''

from uncompyle2 import main, verify
import getopt, sys
import os, time, shutil
from fnmatch import fnmatch

#----- configure this for your needs

lib_prefix = ['.', '/usr/lib/', '/usr/local/lib/']
target_base = '/tmp/py-dis/'

PYC = ('*.pyc', )
PYO = ('*.pyo', )
PYOC = ('*.pyc', '*.pyo')

test_options = {
    # name: (src_basedir, pattern, output_base_suffix)
    'test': ['test', PYC, 'test'],
    '2.5': ['python2.5', PYC, 'python-lib2.5'],
    '2.6': ['python2.6', PYC, 'python-lib2.6'],
    '2.7': ['python2.7', PYC, 'python-lib2.7']
}

#-----

def help():
    print 'Usage-Examples:'
    print 'test_pythonlib --all             # decompile all tests (suite + libs)'
    print 'test_pythonlib --all --verify    # decomyile all tests and verify results'
    print 'test_pythonlib --test            # decompile only the testsuite'
    print 'test_pythonlib --2.2 --verify    # decompile and verify python lib 2.2'

def do_tests(src_dir, patterns, target_dir, start_with=None, do_verify=0):
    def visitor(files, dirname, names):
        files.extend(
            [os.path.normpath(os.path.join(dirname, n))
                 for n in names
                    for pat in patterns
                        if fnmatch(n, pat)])

    files = []
    cwd = os.getcwd()
    os.chdir(src_dir)
    os.path.walk(os.curdir, visitor, files)
    os.chdir(cwd)
    files.sort()

    if start_with:
        try:
            start_with = files.index(start_with)
            files = files[start_with:]
            print '>>> starting with file', files[0]
        except ValueError:
            pass

    print time.ctime()
    print 'Working directory: ', src_dir
    try:
        main(src_dir, target_dir, files, [], do_verify=do_verify)
    except (KeyboardInterrupt, OSError):
        print 
        exit(1)
    
if __name__ == '__main__':
    do_verify = 0
    test_dirs = []
    checked_dirs = []
    start_with = None

    test_options_keys = test_options.keys(); test_options_keys.sort()
    opts, args = getopt.getopt(sys.argv[1:], '',
                               ['start-with=', 'verify', 'all', ] \
                               + test_options_keys )
    if not opts:
        help()
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
        else:
            help()

    for src_dir, pattern, target_dir in test_dirs:
        for libpath in lib_prefix:
            testpath = os.path.join(libpath, src_dir)
            testlibfile = "%s/%s" % (testpath, 'os.py')
            testfile = "%s/%s" % (testpath, 'test_empty.py')
            if os.path.exists(testlibfile) or os.path.exists(testfile):
                src_dir = testpath
                checked_dirs.append([src_dir, pattern, target_dir])
                break

    for src_dir, pattern, target_dir in checked_dirs:
        target_dir = os.path.join(target_base, target_dir)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir, ignore_errors=1)
        do_tests(src_dir, pattern, target_dir, start_with, do_verify)
