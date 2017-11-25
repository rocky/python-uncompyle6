#!/bin/bash
me=${BASH_SOURCE[0]}

# Python version setup
FULLVERSION=${1:-2.7.14}
PYVERSION=${FULLVERSION%.*}
MINOR=${FULLVERSION##?.?.}

typeset -i STOP_ONERROR=1
typeset -A SKIP_TESTS=( [test_aepack.py]=1 [audiotests.py]=1)

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
for file in test_*.py; do
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
