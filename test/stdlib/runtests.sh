#!/bin/bash
me=${BASH_SOURCE[0]}

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

typeset -A SKIP_TESTS
case $PYVERSION in
    2.4)
	. ./2.4-exclude.sh
	;;
    2.5)
	. ./2.5-exclude.sh
	;;
    2.6)
	. ./2.6-exclude.sh
	;;
    2.7)
	. ./2.7-exclude.sh
	;;
    3.0)
	SKIP_TESTS=(
	    [test_array.py]=1  # Handling of bytestring
	    [test_binascii.py]=1 # handling of bytearray?
	    [test_concurrent_futures.py]=1 # too long to run over 46 seconds by itself
	    [test_datetimetester.py]=1
	    [test_decimal.py]=1
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_fileio.py]=1
	)
	if (( BATCH )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	fi
	;;
    3.1)
	SKIP_TESTS=(
	    [test_concurrent_futures.py]=1 # too long to run over 46 seconds by itself
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_fileio.py]=1
	)
	if (( BATCH )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	fi
	;;
    3.2)
	. ./3.2-exclude.sh
	;;
    3.3)
	. ./3.3-exclude.sh
	;;
    3.4)
	. ./3.4-exclude.sh
	;;
    3.5)
	. ./3.5-exclude.sh
	;;
    3.6)
	. ./3.6-exclude.sh
	;;
    3.7)
	. ./3.7-exclude.sh
	;;
    3.8)
	. ./3.8-exclude.sh
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
OPTS=${OPTS:-""}
TESTDIR=/tmp/test${PYVERSION}
if [[ -e $TESTDIR ]] ; then
    rm -fr $TESTDIR
fi

PYENV_ROOT=${PYENV_ROOT:-$HOME/.pyenv}
pyenv_local=$(pyenv local)

echo Python version is $pyenv_local

# pyenv version update
for dir in ../ ../../ ; do
    cp -v .python-version $dir
done


mkdir $TESTDIR || exit $?
cp -r ${PYENV_ROOT}/versions/${PYVERSION}.${MINOR}/lib/python${PYVERSION}/test $TESTDIR
if [[ $PYVERSION == 3.2 ]] ; then
    cp ${PYENV_ROOT}/versions/${PYVERSION}.${MINOR}/lib/python${PYVERSION}/test/* $TESTDIR
    cd $TESTDIR
else
    cd $TESTDIR/test
fi
pyenv local $FULLVERSION
export PYTHONPATH=$TESTDIR
export PATH=${PYENV_ROOT}/shims:${PATH}

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
else
    files=$(echo test_*.py)
fi

typeset -i ALL_FILES_STARTTIME=$(date +%s)
typeset -i skipped=0

NOT_INVERTED_TESTS=${NOT_INVERTED_TESTS:-1}

for file in $files; do
    # AIX bash doesn't grok [[ -v SKIP... ]]
    [[ -z ${SKIP_TESTS[$file]} ]] && SKIP_TESTS[$file]=0
    if [[ ${SKIP_TESTS[$file]} == ${NOT_INVERTED_TESTS} ]] ; then
	((skipped++))
	continue
    fi

    # If the fails *before* decompiling, skip it!
    typeset -i STARTTIME=$(date +%s)
    if [ ! -r $file ]; then
	echo "Skipping test $file -- not readable. Does it exist?"
	continue
    elif ! python $file >/dev/null 2>&1 ; then
	echo "Skipping test $file -- it fails on its own"
	continue
    fi
    typeset -i ENDTIME=$(date +%s)
    typeset -i time_diff
    (( time_diff =  ENDTIME - STARTTIME))
    if (( time_diff > $timeout )) ; then
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
    $DECOMPILER $OPTS $decompiled_file > $file
    rc=$?
    if (( rc == 0 )) ; then
	echo ========== $(date +%X) Running $file ===========
	timeout_cmd python $file
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
cd $fulldir/../.. && pyenv local $FULLVERSION
exit $allerrs
