#!/bin/bash
me=${BASH_SOURCE[0]}

typeset -i batch=1
isatty=$(/usr/bin/tty 2>/dev/null)
if [[ -n $isatty ]] && [[ "$isatty" != 'not a tty' ]] ; then
    batch=0
fi


function displaytime {
  local T=$1
  local D=$((T/60/60/24))
  local H=$((T/60/60%24))
  local M=$((T/60%60))
  local S=$((T%60))
  (( $D > 0 )) && printf '%d days ' $D
  (( $H > 0 )) && printf '%d hours ' $H
  (( $M > 0 )) && printf '%d minutes ' $M
  (( $D > 0 || $H > 0 || $M > 0 )) && printf 'and '
  printf '%d seconds\n' $S
}

# Python version setup
FULLVERSION=$(pyenv local)
PYVERSION=${FULLVERSION%.*}
MINOR=${FULLVERSION##?.?.}

STOP_ONERROR=${STOP_ONERROR:-1}

typeset -A SKIP_TESTS
case $PYVERSION in
    2.4)
	SKIP_TESTS=(
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_grp.py]=1      # Long test - might work Control flow?
	    [test_pep247.py]=1 # Long test - might work? Control flow?
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_pyclbr.py]=1 # Investigate
	    [test_socketserver.py]=1 # -- test takes too long to run: 40 seconds
	    [test_threading.py]=1 # test takes too long to run: 11 seconds
	    [test_thread.py]=1 # test takes too long to run: 36 seconds
	    [test_trace.py]=1 # Long test - works
	    [test_zipfile64.py]=1  # Runs ok but takes 204 seconds
	)
	;;
    2.5)
	SKIP_TESTS=(
	    [test_dis.py]=1        # We change line numbers - duh!
	    [test_grammar.py]=1    # Too many stmts. Handle large stmts
	    [test_grp.py]=1        # Long test - might work Control flow?
	    [test_pdb.py]=1        # Line-number specific
	    [test_pep247.py]=1     # "assert xxx or .." not detected properly in check_hash_module()
	    [test_pep352.py]=1     # Investigate
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_pyclbr.py]=1 # Investigate
	    [test_struct.py]=1 # "if and" confused for if .. assert and
	    [test_threading.py]=1 # test takes too long to run: 11 seconds
	    [test_thread.py]=1 # test takes too long to run: 36 seconds
	    [test_trace.py]=1  # Line numbers are expected to be different
	    [test_zipfile64.py]=1  # Runs ok but takes 204 seconds
	)
	;;
    2.6)
	SKIP_TESTS=(
	    [test_aepack.py]=1 # Fails on its own
	    [test_codeccallbacks.py]=1  # Fails on its own
	    [test_compile.py]=1  # Intermittent - sometimes works and sometimes doesn't
	    [test_exceptions.py]=1
	    [test_grp.py]=1      # Long test - might work Control flow?
	    [test_pep352.py]=1     # Investigate
	    [test_pprint.py]=1
	    [test_pyclbr.py]=1 # Investigate
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_trace.py]=1  # Line numbers are expected to be different
	    [test_urllib2net.py]=1 # Fails on its own. May need interactive input
	    [test_zipfile64.py]=1  # Skip Long test
	    [test_zlib.py]=1  # Takes too long to run (more than 3 minutes 39 seconds)
	    # .pyenv/versions/2.6.9/lib/python2.6/lib2to3/refactor.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/pyclbr.pyc
	)
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_aifc.py]=1
	    SKIP_TESTS[test_array.py]=1

	    # SyntaxError: Non-ASCII character '\xdd' in file test_base64.py on line 153, but no encoding declared; see http://www.python.org/peps/pep-0263.html for details
	    SKIP_TESTS[test_base64.py]=1

	    # output indicates expected == output, but this fails anyway.
	    # Maybe the underlying encoding is subtlely different so it
	    # looks the same?
	    SKIP_TESTS[test_pprint.py]=1
	fi
	;;
    2.7)
	SKIP_TESTS=(
	    # These are ok, but our test machine POWER has problems
	    # so we skip..
	    [test_httplib.py]=1  # Ok, but POWER has problems with this
	    [test_pdb.py]=1 # Ok, but POWER has problems with this

	    [test_capi.py]=1
	    [test_curses.py]=1  # Possibly fails on its own but not detected
	    [test test_cmd_line.py]=1 # Takes too long, maybe hangs, or looking for interactive input?
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_doctest.py]=1 # Fails on its own
	    [test_exceptions.py]=1
	    [test_format.py]=1  # control flow. uncompyle2 does not have problems here
	    [test_grammar.py]=1     # Too many stmts. Handle large stmts
	    [test_grp.py]=1     # test takes to long, works interactively though
	    [test_io.py]=1 # Test takes too long to run
	    [test_ioctl.py]=1 # Test takes too long to run
	    [test_long.py]=1
	    [test_long_future.py]=1
	    [test_math.py]=1
	    [test_memoryio.py]=1 # FIX
	    [test_modulefinder.py]=1 # FIX
	    [test_multiprocessing.py]=1 # On uncompyle2, takes 24 secs
	    [test_pwd.py]=1     # Takes too long
	    [test_pty.py]=1
	    [test_runpy.py]=1   # Long and fails on its own
	    [test_select.py]=1  # Runs okay but takes 11 seconds
	    [test_socket.py]=1  # Runs ok but takes 22 seconds
	    [test_subprocess.py]=1 # Runs ok but takes 22 seconds
	    [test_sys_setprofile.py]=1
	    [test_sys_settrace.py]=1 # Line numbers are expected to be different
	    [test_traceback.py]=1 # Line numbers change - duh.
	    [test_unicode.py]=1  # Too long to run 11 seconds
	    [test_xpickle.py]=1 # Runs ok but takes 72 seconds
	    [test_zipfile64.py]=1  # Runs ok but takes 204 seconds
        )
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_array.py]=1
	    SKIP_TESTS[test_ast.py]=1
	    SKIP_TESTS[test_audioop.py]=1

	    # SyntaxError: Non-ASCII character '\xdd' in file test_base64.py on line 153, but no encoding declared; see http://www.python.org/peps/pep-0263.html for details
	    SKIP_TESTS[test_base64.py]=1
	fi
	;;
    3.3)
	SKIP_TESTS=(
	    [test_atexit.py]=1  #
	    [test_decorators.py]=1  # Control flow wrt "if elif"
	)
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	fi
	;;

    3.5)
	SKIP_TESTS=(
	    [test_atexit.py]=1  #
	    [test_decorators.py]=1  # Control flow wrt "if elif"
	)
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	fi
	;;

    3.6)
	SKIP_TESTS=(
	    [test_contains.py]=1    # Code "while False: yield None" is optimized away in compilation
	    [test_decorators.py]=1  # Control flow wrt "if elif"
	    [test_pow.py]=1         # Control flow wrt "continue"
	    [test_quopri.py]=1      # Only fails on POWER
	)
	;;
    3.7)
	SKIP_TESTS=(
	    [test_argparse.py]=1  #
	    [test_ast.py]=1  #
	    [test_contains.py]=1    # Code "while False: yield None" is optimized away in compilation
 	    [test_decorators.py]=1  # Control flow wrt "if elif"
	)
	;;
    *)
	SKIP_TESTS=( [test_aepack.py]=1
		     [audiotests.py]=1
		     [test_dis.py]=1   # We change line numbers - duh!
		     [test_generators.py]=1  # I think string formatting of docstrings gets in the way. Not sure
		   )
	;;
esac

# Test directory setup
srcdir=$(dirname $me)
cd $srcdir
fulldir=$(pwd)

# DECOMPILER=uncompyle2
DECOMPILER=${DECOMPILER:-"$fulldir/../../bin/uncompyle6"}
TESTDIR=/tmp/test${PYVERSION}
if [[ -e $TESTDIR ]] ; then
    rm -fr $TESTDIR
fi

PYENV_ROOT=${PYENV_ROOT:-$HOME/.pyenv}
pyenv_local=$(pyenv local)
mkdir $TESTDIR || exit $?
cp -r ${PYENV_ROOT}/versions/${PYVERSION}.${MINOR}/lib/python${PYVERSION}/test $TESTDIR
cd $TESTDIR/test
pyenv local $FULLVERSION
export PYTHONPATH=$TESTDIR
export PATH=${PYENV_ROOT}/shims:${PATH}

# Run tests
typeset -i i=0
typeset -i allerrs=0
if [[ -n $1 ]] ; then
    files=$1
    typeset -a files_ary=( $(echo $1) )
    if (( ${#files_ary[@]} == 1 )) ; then
	SKIP_TESTS=()
    fi
else
    files=$(echo test_*.py)
fi

typeset -i ALL_FILES_STARTTIME=$(date +%s)
typeset -i skipped=0

for file in $files; do
    # AIX bash doesn't grok [[ -v SKIP... ]]
    if [[ ${SKIP_TESTS[$file]} == 1 ]] ; then
	((skipped++))
	continue
    fi

    # If the fails *before* decompiling, skip it!
    typeset -i STARTTIME=$(date +%s)
    if ! python $file >/dev/null 2>&1 ; then
	echo "Skipping test $file -- it fails on its own"
	continue
    fi
    typeset -i ENDTIME=$(date +%s)
    typeset -i time_diff
    (( time_diff =  ENDTIME - STARTTIME))
    if (( time_diff > 10 )) ; then
	echo "Skipping test $file -- test takes too long to run: $time_diff seconds"
	continue
    fi

    ((i++))
    # (( i > 40 )) && break
    short_name=$(basename $file .py)
    decompiled_file=$short_name-${PYVERSION}.pyc
    $fulldir/compile-file.py $file && \
    mv $file{,.orig} && \
    echo ==========  $(date +%X) Decompiling $file ===========
    $DECOMPILER $decompiled_file > $file
    rc=$?
    if (( rc == 0 )) ; then
	echo ========== $(date +%X) Running $file ===========
	python $file
	rc=$?
    else
	echo ======= Skipping $file due to compile/decompile errors ========
    fi
    (( rc != 0 && allerrs++ ))
    if (( STOP_ONERROR && rc )) ; then
	echo "** Ran $i tests before failure. Skipped $skipped test for known failures. **"
	exit $allerrs
    fi
done
typeset -i ALL_FILES_ENDTIME=$(date +%s)

(( time_diff =  ALL_FILES_ENDTIME - ALL_FILES_STARTTIME))

printf "Ran $i unit-test files in "
displaytime $time_diff
echo "Skipped $skipped test for known failures."
exit $allerrs
