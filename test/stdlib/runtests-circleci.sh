#!/bin/bash
me=${BASH_SOURCE[0]}

# Note: for 2.6 sometimes we need to set PYTHON=pytest
PYTHON=${PYTHON:-python}

typeset -i BATCH=${BATCH:-0}
if (( ! BATCH )) ; then
    isatty=$(/usr/bin/tty 2>/dev/null)
    if [[ -n $isatty ]] && [[ "$isatty" != 'not a tty' ]] ; then
	BATCH=0
    fi
fi


function displaytime {
  local T=$1
  local D=$((T/60/60/24))
  local H=$((T/60/60%24))
  local M=$((T/60%60))
  local S=$((T%60))
  (( D > 0 )) && printf '%d days ' $D
  (( H > 0 )) && printf '%d hours ' $H
  (( M > 0 )) && printf '%d minutes ' $M
  (( D > 0 || H > 0 || M > 0 )) && printf 'and '
  printf '%d seconds\n' $S
}

FULLVERSION=2.7.18
IS_PYPY=0
MINOR=${FULLVERSION##?.?.}

STOP_ONERROR=${STOP_ONERROR:-1}

typeset -i timeout=15

function timeout_cmd {

  (
    $@ &
    child=$!
    trap -- "" SIGTERM
    (
	sleep "$timeout"
	if ps -p $child >/dev/null ; then
	    echo ""
	    echo >&1 "**Killing ${2}; takes more than $timeout seconds to run"
	    kill -TERM ${child}
	fi
    ) &
    wait "$child"
  )
}

. ./2.7-exclude.sh

# Test directory setup
srcdir=$(dirname $me)
cd $srcdir
fulldir=$(pwd)

# DECOMPILER=uncompyle2
DECOMPILER=${DECOMPILER:-"$fulldir/../../bin/uncompyle6"}
OPTS=${OPTS:-""}
TESTDIR=/tmp/test2.7
if [[ -e $TESTDIR ]] ; then
    rm -fr $TESTDIR
fi

mkdir $TESTDIR || exit $?
(cd /usr/local/lib/python2.7/site-packages && cp */test*.pyc $TESTDIR)
(cd /usr/local/lib/python2.7/site-packages && cp */*/test*.pyc $TESTDIR)
cd $TESTDIR
export PATH=/usr/local/bin/python:${PATH}

DONT_SKIP_TESTS=${DONT_SKIP_TESTS:-0}

# Run tests
typeset -i i=0
typeset -i allerrs=0
if [[ -n $1 ]] ; then
    files=$@
    typeset -a files_ary=( $(echo $@) )
    if (( ${#files_ary[@]} == 1 || DONT_SKIP_TESTS == 1 )) ; then
	SKIP_TESTS=()
    fi
elif [[ "$CIRCLECI" == "true" ]] ; then
    files=$(echo test_*.pyc)
else
    files=$(echo test_*.py)
fi

typeset -i ALL_FILES_STARTTIME=$(date +%s)
typeset -i skipped=0

NOT_INVERTED_TESTS=${NOT_INVERTED_TESTS:-1}

for file in $files; do
    # If the fails *before* decompiling, skip it!
    typeset -i STARTTIME=$(date +%s)
    if [ ! -r $file ]; then
	echo "Skipping test $file -- not readable. Does it exist?"
	continue
    elif ! $PYTHON $file >/dev/null 2>&1 ; then
	echo "Skipping test $file -- it fails on its own"
	continue
    fi
    typeset -i ENDTIME=$(date +%s)
    typeset -i time_diff
    (( time_diff =  ENDTIME - STARTTIME))
    if (( time_diff > timeout )) ; then
	echo "Skipping test $file -- test takes too long to run: $time_diff seconds"
	continue
    fi

    ((i++))
    # (( i > 40 )) && break
    short_name=$(basename $file .py)
    if ((IS_PYPY)); then
	decompiled_file=$short_name-${MAJOR}.${MINOR}.pyc
    else
	decompiled_file=$short_name-${PYVERSION}.pyc
    fi
    $fulldir/compile-file.py $file && \
    mv $file{,.orig} && \
    echo ==========  $(date +%X) Decompiling $file ===========
    $DECOMPILER $OPTS $decompiled_file > $file 2>/dev/null
    rc=$?
    if (( rc == 0 )) ; then
	echo ========== $(date +%X) Running $file ===========
	timeout_cmd $PYTHON $file
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

printf "Ran $i unit-test files, $allerrs errors; Elapsed time: "
displaytime $time_diff
echo "Skipped $skipped test for known failures."
exit $allerrs
