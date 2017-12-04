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
	    [test_extcall.py]=1  # TypeError: saboteur() takes no arguments (1 given)
	    [test_format.py]=1   # Control flow?
	    [test_grp.py]=1      # Long test - might work Control flow?
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
	    [test_cgi.py]=1    # need to fix tryelse
	    [test_codecs.py]=1    # need to fix tryelse
	    [test_decorators.py]=1   # Syntax error decorators?
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_extcall.py]=1  # TypeError: saboteur() takes no arguments (1 given)
	    [test_format.py]=1   # Control flow?
	    [test_grp.py]=1      # Long test - might work Control flow?
	    [test_long_future.py]=1 # Control flow?
	    [test_math.py]=1 # Control flow?
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_queue.py]=1 # Control flow?
	    [test_sax.py]=1  # Control flow?
	    [test_types.py]=1 # Control flow?
	)
    2.6)
	SKIP_TESTS=(
	    [test_binop.py]=1  # need to fix tryelse
	    [test_cmath.py]=1 # Control flow?
	    [test_codecs.py]=1    # need to fix tryelse
	    [test_coercion.py]=1    # Control flow?
	    [test_cookielib.py]=1    # Control flow?
	    [test_contextlib.py]=1  # decorators
            [test_decorators.py]=1  # decorators
            [test_enumerate.py]=1  # Control flow?
	    [test_file.py]=1   # Control flow?
	    [test_format.py]=1   # Control flow?
	    [test_frozen.py]=1  # Control flow?
	    [test_ftplib.py]=1  # Control flow?
	    [test_funcattrs.py]=1  # Control flow?
	    [test_future4.py]=1  # Possible additional rule for future mechanism?
	    [test_grp.py]=1      # Long test - might work Control flow?
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_queue.py]=1 # Control flow?
	    )
	;;
    2.7)
	SKIP_TESTS=(
	    [test_builtin.py]=1
	    [test_contextlib.py]=1  # decorators
            [test_decorators.py]=1  # decorators
	    [test_descr.py]=1 # syntax error look at
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_future4.py]=1  # Possible additional rule for future mechanism?
	    [test_grammar.py]=1  # Long test look at
	    [test_importlib.py]=1  # Control flow?
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
    if ! python $file >/dev/null 2>&1 ; then
	continue
    fi

    ((i++))
    # (( i > 40 )) && break
    short_name=$(basename $file .py)
    decompiled_file=$short_name-${PYVERSION}.pyc
    $fulldir/compile-file.py $file && \
    mv $file{,.orig} && \
    $fulldir/../../bin/uncompyle6 $decompiled_file > $file
    rc=$?
    if (( rc == 0 )) ; then
	echo ========== Running $file ===========
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
