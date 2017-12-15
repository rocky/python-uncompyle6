#!/bin/bash
me=${BASH_SOURCE[0]}

# Python version setup
FULLVERSION=$(pyenv local)
PYVERSION=${FULLVERSION%.*}
MINOR=${FULLVERSION##?.?.}

typeset -i STOP_ONERROR=1

typeset -A SKIP_TESTS
case $PYVERSION in
    2.4)
	SKIP_TESTS=(
	    [test_binop.py]=1  # need to fix tryelse
	    [test_cgi.py]=1    # need to fix tryelse
	    [test_codecs.py]=1    # need to fix tryelse
	    [test_decorators.py]=1   # Syntax error decorators?
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_frozen.py]=1
	    [test_grp.py]=1      # Long test - might work Control flow?
	    [test_imp.py]=1   # Control flow?
	    [test_import.py]=1   # Control flow?
	    [test_long_future.py]=1 # Control flow?
	    [test_math.py]=1 # Control flow?
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_queue.py]=1 # Control flow?
	    [test_sax.py]=1  # Control flow?
	    # [test_threading.py]=1 # Long test - works
	    [test_types.py]=1 # Control flow?
	)
	;;
    2.5)
	SKIP_TESTS=(
	    [test_binop.py]=1  # need to fix tryelse
	    [test_cgi.py]=1    # need to fix tryelse
	    [test_codecs.py]=1    # need to fix tryelse
	    [test_coercion.py]=1
	    [test_contextlib.py]=1
	    [test_decorators.py]=1   # Syntax error decorators?
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_exceptions.py]=1
	    [test_format.py]=1   # Control flow?
	    [test_frozen.py]=1
	    [test_functools.py]=1
	    [test_grammar.py]=1  # Too many stmts. Handle large stmts
	    [test_grp.py]=1      # Long test - might work Control flow?
	    [test_imp.py]=1
	    [test_long_future.py]=1 # Control flow?
	    [test_math.py]=1 # Control flow?
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_queue.py]=1 # Control flow?
	    [test_re.py]=1 # Probably Control flow?
	    [test_sax.py]=1  # Control flow?
	    [test_trace.py]=1  # Line numbers are expected to be different
	    [test_types.py]=1 # Control flow?
	    [test_zipfile64.py]=1  # Runs ok but takes 204 seconds
	)
	;;
    2.6)
	SKIP_TESTS=(
	    [test_binop.py]=1  # need to fix tryelse
	    [test_cmath.py]=1 # Control flow?
	    [test_codecs.py]=1    # need to fix tryelse
	    [test_coercion.py]=1    # Control flow?
	    [test_cookielib.py]=1    # Control flow?
            [test_decorators.py]=1  # Syntax Error - look at
            [test_enumerate.py]=1  # Control flow?
	    [test_file.py]=1   # Control flow?
	    [test_format.py]=1   # Control flow?
	    [test_frozen.py]=1  # Control flow?
	    [test_ftplib.py]=1  # Control flow?
	    [test_funcattrs.py]=1  # Control flow?
	    [test_grp.py]=1      # Long test - might work Control flow?
	    [test_imp.py]=1
	    [test_int.py]=1
	    [test_long.py]=1
	    [test_pty.py]=1
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_queue.py]=1 # Control flow?
	    [test_re.py]=1 # Probably Control flow?
	    [test_strftime.py]=1
	    [test_trace.py]=1  # Line numbers are expected to be different
	    # .pyenv/versions/2.6.9/lib/python2.6/lib2to3/refactor.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/mailbox.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/markupbase.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/pstats.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/pyclbr.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/quopri.pyc -- look at ishex, is short
	    # .pyenv/versions/2.6.9/lib/python2.6/random.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/smtpd.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/sre_parse.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/tabnanny.pyc
	    # .pyenv/versions/2.6.9/lib/python2.6/tarfile.pyc
	    )
	;;
    2.7)
	SKIP_TESTS=(
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_doctest.py]=1
	    [test_grammar.py]=1  # Too many stmts. Handle large stmts
	    [test_io.py]=1 # Test takes too long to run
	    [test_ioctl.py]=1 # Test takes too long to run
	    [test_itertools.py]=1 # Syntax error - look at!
	    [test_memoryio.py]=1 # ?
	    [test_multiprocessing.py]=1 # ?
	    [test_pep352.py]=1 # ?
	    [test_re.py]=1 # ?
	    [test_sys_settrace.py]=1 # Line numbers are expected to be different
	    [test_strtod.py]=1
	    [test_traceback.py]=1
	    [test_unicode.py]=1
	    [test_zipfile64.py]=1  # Runs ok but takes 204 seconds
	    # Syntax errors:
	    # .pyenv/versions/2.7.14/lib/python2.7/mimify.pyc
	    # .pyenv/versions/2.7.14/lib/python2.7/netrc.pyc
	    # .pyenv/versions/2.7.14/lib/python2.7/pyclbr.pyc
	    # .pyenv/versions/2.7.14/lib/python2.7/sre_compile.pyc
        )
	;;
    *)
	SKIP_TESTS=( [test_aepack.py]=1 [audiotests.py]=1
		     [test_dis.py]=1   # We change line numbers - duh!
		   )
	;;
esac

# Test directory setup
srcdir=$(dirname $me)
cd $srcdir
fulldir=$(pwd)

# DECOMPILER=uncompyle2
DECOMPILER="$fulldir/../../bin/uncompyle6"
TESTDIR=/tmp/test${PYVERSION}
if [[ -e $TESTDIR ]] ; then
    rm -fr $TESTDIR
fi
mkdir $TESTDIR || exit $?
cp -r ~/.pyenv/versions/${PYVERSION}.${MINOR}/lib/python${PYVERSION}/test $TESTDIR
cd $TESTDIR/test
export PYTHONPATH=$TESTDIR

# Run tests
typeset -i i=0
typeset -i allerrs=0
if [[ -n $1 ]] ; then
    files=$1
    SKIP_TESTS=()
else
    files=test_*.py
fi
for file in $files; do
    [[ -v SKIP_TESTS[$file] ]] && continue

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
	echo "** Ran $i tests before failure **"
	exit $allerrs
    fi
done
echo "Ran $i tests"
exit $allerrs
