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
	SKIP_TESTS=( [test_binop.py]=1  # need to fix tryelse
		     [test_bool.py]=1   # need to fix tryelse
		     [test_call.py]=1   # need to fix tryelse
		     [test_cgi.py]=1    # need to fix tryelse
		     [test_class.py]=1  # need to fix tryelse
		   )
	;;
    2.6)
	SKIP_TESTS=( [test_array.py]=1 [test_asyncore.py]=1)
	;;
    2.7)
	SKIP_TESTS=(
	    [test_builtin.py]=1
	    [test_contextlib.py]=1  # decorators
            [test_decorators.py]=1  # decorators
	    [test_decimal.py]=1
	    [test_descr.py]=1 # syntax error look at
        )
	;;
    *)
	SKIP_TESTS=( [test_aepack.py]=1 [audiotests.py]=1)
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
