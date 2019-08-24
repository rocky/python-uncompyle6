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

typeset -i STOP_ONERROR=1

typeset -A SKIP_TESTS
case $PYVERSION in
    2.4)
	SKIP_TESTS=(
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_grp.py]=1      # Long test - might work Control flow?
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_pep247.py]=1 # Long test - might work? Control flow?
	    [test_queue.py]=1 # Control flow?
	    # [test_threading.py]=1 # Long test - works
	)
	;;
    2.5)
	SKIP_TESTS=(
	    [test_contextlib.py]=1 # Syntax error - look at
	    [test_dis.py]=1        # We change line numbers - duh!
	    [test_grammar.py]=1    # Too many stmts. Handle large stmts
	    [test_grp.py]=1        # Long test - might work Control flow?
	    [test_pdb.py]=1        # Line-number specific
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_queue.py]=1 # Control flow?
	    [test_re.py]=1 # Probably Control flow?
	    [test_trace.py]=1  # Line numbers are expected to be different
	    [test_zipfile64.py]=1  # Runs ok but takes 204 seconds
	)
	;;
    2.6)
	SKIP_TESTS=(
	    [test_aepack.py]=1
	    [test_aifc.py]=1
	    [test_array.py]=1
	    [test_audioop.py]=1
	    [test_base64.py]=1
	    [test_bigmem.py]=1
	    [test_binascii.py]=1
	    [test_builtin.py]=1
	    [test_bytes.py]=1
	    [test_class.py]=1
	    [test_codeccallbacks.py]=1
	    [test_codecencodings_cn.py]=1
	    [test_codecencodings_hk.py]=1
	    [test_codecencodings_jp.py]=1
	    [test_codecencodings_kr.py]=1
	    [test_codecencodings_tw.py]=1
	    [test_codecencodings_cn.py]=1
	    [test_codecmaps_hk.py]=1
	    [test_codecmaps_jp.py]=1
	    [test_codecmaps_kr.py]=1
	    [test_codecmaps_tw.py]=1
	    [test_codecs.py]=1
	    [test_compile.py]=1  # Intermittent - sometimes works and sometimes doesn't
	    [test_cookielib.py]=1
	    [test_copy.py]=1
	    [test_decimal.py]=1
	    [test_descr.py]=1    # Problem in pickle.py?
	    [test_exceptions.py]=1
	    [test_extcall.py]=1
	    [test_float.py]=1
	    [test_future4.py]=1
	    [test_generators.py]=1
	    [test_grp.py]=1      # Long test - might work Control flow?
	    [test_opcodes.py]=1
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_re.py]=1 # Probably Control flow?
	    [test_queue.py]=1 # Control flow?
	    [test_trace.py]=1  # Line numbers are expected to be different
	    [test_zipfile64.py]=1  # Skip Long test
	    [test_zlib.py]=1  # Takes too long to run (more than 3 minutes 39 seconds)
	    # .pyenv/versions/2.6.9/lib/python2.6/lib2to3/refactor.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/pyclbr.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/quopri.pyc -- look at ishex, is short
	    # .pyenv/versions/2.6.9/lib/python2.6/random.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/smtpd.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/sre_parse.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/tabnanny.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/tarfile.pyc

	    # Not getting set by bach below?
	    [test_pprint.py]=1

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
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_doctest.py]=1 # Fails on its own
	    [test_exceptions.py]=1
	    [test_format.py]=1  # control flow. uncompyle2 does not have problems here
	    [test_generators.py]=1  # control flow. uncompyle2 has problem here too
	    [test_grammar.py]=1     # Too many stmts. Handle large stmts
	    [test_io.py]=1 # Test takes too long to run
	    [test_ioctl.py]=1 # Test takes too long to run
	    [test_itertools.py]=1 # Fix erroneous reduction to "conditional_true".
	                          # See test/simple_source/bug27+/05_not_unconditional.py
	    [test_long.py]=1
	    [test_long_future.py]=1
	    [test_math.py]=1
	    [test_memoryio.py]=1 # FIX
	    [test_multiprocessing.py]=1 # On uncompyle2, taks 24 secs
	    [test_pep352.py]=1  # ?
	    [test_posix.py]=1   # Bug in try-else detection inside test_initgroups()
	                        # Deal with when we have better flow-control detection
	    [test_pwd.py]=1     # Takes too long
	    [test_pty.py]=1
	    [test_queue.py]=1   # Control flow?
	    [test_re.py]=1      # Probably Control flow?
	    [test_runpy.py]=1   # Long and fails on its own
	    [test_select.py]=1  # Runs okay but takes 11 seconds
	    [test_socket.py]=1  # Runs ok but takes 22 seconds
	    [test_subprocess.py]=1 # Runs ok but takes 22 seconds
	    [test_sys_setprofile.py]=1
	    [test_sys_settrace.py]=1 # Line numbers are expected to be different
	    [test_strtod.py]=1 # FIX
	    [test_traceback.py]=1 # Line numbers change - duh.
	    [test_types.py]=1     # try/else confusions
	    [test_unicode.py]=1  # Too long to run 11 seconds
	    [test_xpickle.py]=1 # Runs ok but takes 72 seconds
	    [test_zipfile64.py]=1  # Runs ok but takes 204 seconds
	    [test_zipimport.py]=1  # We can't distinguish try from try/else yet
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
    3.5)
	SKIP_TESTS=(
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
mkdir $TESTDIR || exit $?
cp -r ${PYENV_ROOT}/versions/${PYVERSION}.${MINOR}/lib/python${PYVERSION}/test $TESTDIR
cd $TESTDIR/test
pyenv local $FULLVERSION
export PYTHONPATH=$TESTDIR

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
    files=test_*.py
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
