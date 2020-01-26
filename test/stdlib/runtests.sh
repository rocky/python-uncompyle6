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
	SKIP_TESTS=(
	    [test_decimal.py]=1  #
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_generators.py]=1  # Investigate
	    [test_grammar.py]=1    # Too many stmts. Handle large stmts
	    [test_grp.py]=1      # Long test - might work Control flow?
	    [test_pep247.py]=1 # Long test - might work? Control flow?
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_socketserver.py]=1 # -- test takes too long to run: 40 seconds
	    [test_threading.py]=1 # test takes too long to run: 11 seconds
	    [test_thread.py]=1 # test takes too long to run: 36 seconds
	    [test_trace.py]=1 # Long test - works
	    [test_zipfile64.py]=1  # Runs ok but takes 204 seconds
	)
	;;
    2.5)
	. ./2.5-exclude.sh
	;;
    2.6)
	. ./2.6-exclude.sh
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_aifc.py]=1
	    SKIP_TESTS[test_array.py]=1

	    # SyntaxError: Non-ASCII character '\xdd' in file test_base64.py on line 153, but no encoding declared; see http://www.python.org/peps/pep-0263.html for details
	    SKIP_TESTS[test_base64.py]=1
	    SKIP_TESTS[test_decimal.py]=1 # Might be a POWER math thing

	    # output indicates expected == output, but this fails anyway.
	    # Maybe the underlying encoding is subtlely different so it
	    # looks the same?
	fi
	;;
    2.7)
	. ./2.7-exclude.sh
	# About 335 unit-test remaining files run in about 20 minutes and 11 seconds
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_array.py]=1
	    SKIP_TESTS[test_ast.py]=1
	    SKIP_TESTS[test_audioop.py]=1
	    SKIP_TESTS[test_doctest2.py]=1 # a POWER thing?
	    SKIP_TESTS[test_httplib.py]=1  # Ok, but POWER has problems with this
	    SKIP_TESTS[test_pdb.py]=1 # Ok, but POWER has problems with this

	    # SyntaxError: Non-ASCII character '\xdd' in file test_base64.py on line 153, but no encoding declared; see http://www.python.org/peps/pep-0263.html for details
	    SKIP_TESTS[test_base64.py]=1
	fi
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
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	fi
	;;
    3.1)
	SKIP_TESTS=(
	    [test_concurrent_futures.py]=1 # too long to run over 46 seconds by itself
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_fileio.py]=1
	)
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	fi
	;;
    3.2)
	. ./3.2-exclude.sh
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	fi
	;;

    3.3)
	. ./3.3-exclude.sh
	if (( batch )) ; then
	    SKIP_TESTS[test_ftplib.py]=1  # Runs too long on POWER; over 15 seconds
	    SKIP_TESTS[test_idle.py]=1  # No tk
	    SKIP_TESTS[test_pep352.py]=1  # UnicodeDecodeError may be funny on weird environments
	    SKIP_TESTS[test_pep380.py]=1  # test_delegating_generators_claim_to_be_running ?
	    # Fails in crontab environment?
	    # Figure out what's up here
	    # SKIP_TESTS[test_exception_variations.py]=1
	fi
	;;

    3.4)
	. ./3.4-exclude.sh
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_mailbox.py]=1 # Takes to long on POWER; over 15 secs
	    SKIP_TESTS[test_quopri.py]=1
	fi
	;;
    3.5)
	. ./3.5-exclude.sh
	    # About 240 remaining which can be done in about 10 minutes
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_bisect.py]=1
	    SKIP_TESTS[test_buffer.py]=1  # too long
	    SKIP_TESTS[test_distutils.py]=1

	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	    SKIP_TESTS[test_ioctl.py]=1 # it fails on its own
	    SKIP_TESTS[test_tarfile.py]=1 # too long to run on POWER 15 secs
	    SKIP_TESTS[test_venv.py]=1 # takes too long 11 seconds
	fi
	;;

    3.6)
	. ./3.6-exclude.sh
	if (( batch )) ; then
	    # locale on test machine is probably non-default
	    SKIP_TESTS[test__locale.py]=1
	fi
	;;
    3.7)
	. ./3.7-exclude.sh
	if (( batch )) ; then
	    SKIP_TESTS[test_distutils.py]=1
	    SKIP_TESTS[test_fileio.py]=1
	    SKIP_TESTS[test_zipimport_support.py]=1

	fi
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
TESTDIR=/tmp/test${PYVERSION}
if [[ -e $TESTDIR ]] ; then
    rm -fr $TESTDIR
fi

PYENV_ROOT=${PYENV_ROOT:-$HOME/.pyenv}
pyenv_local=$(pyenv local)

# pyenv version update
for dir in ../ ../../ ; do
    cp -v .python-version $dir
done


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
