#!/bin/bash

function displaytime {
    printf "ran in "
    local T=$1
    ((D=T/60/60/24))
    ((H=T/60/60%24))
    ((M=T/60%60))
    ((S=T%60))
    (( D > 0 )) && printf '%d days ' $D
    (( H > 0 )) && printf '%d hours ' $H
    (( M > 0 )) && printf '%d minutes ' $M
    (( D > 0 || H > 0 || M > 0 )) && printf 'and '
    printf '%d seconds\n' $S
}

bs=${BASH_SOURCE[0]}
if [[ $0 != $bs ]] ; then
    echo "This script should not be *sourced* but run through bash"
    exit 1
fi

mydir=$(dirname $bs)
cd $mydir

branch=$(cat ../.git/HEAD | cut -d'/' -f 3)
if [[ $branch == 'python-2.4' ]]; then
    . ../admin-tools/pyenv-older-versions
elif [[ $branch == 'master' ]]; then
    . ../admin-tools/pyenv-newer-versions
else
    echo &1>2 "Error git branch should either be 'master' or 'python-2.4'; got: '$branch'"
    exit 1
fi

MAIN="test_pyenvlib.py"

USER=${USER:-rocky}
EMAIL=${EMAIL:-rb@dustyfeet.com}
WHAT="uncompyle6 ${MAIN}"
MAX_TESTS=${MAX_TESTS:-800}
export BATCH=1

typeset -i RUN_STARTTIME=$(date +%s)

# PYVERSIONS="3.5.6"
MAILBODY=/tmp/${MAIN}-mailbody-$$.txt
# for VERSION in 3.3.7 ; do
for VERSION in $PYVERSIONS ; do
    typeset -i rc=0
    LOGFILE=/tmp/${MAIN}-$VERSION-$$.log

    case "$VERSION" in
	3.7.8 | 3.8.5 | 3.1.5 | 3.0.1 )
	    continue
	    ;;
	3.5.9 )
	    MAX_TESTS=900
	    ;;
	3.2.6 )
	    MAX_TESTS=900
	    ;;
	3.3.7 )
	    MAX_TESTS=1300 # About 1256 exist
	    ;;
	3.4.10 )
	    MAX_TESTS=800
	    ;;
	3.6.11 )
	    # MAX_TESTS=1300  # about 2139 exist
	    # fails on _pyio.cpython-36.opt-1.pyc
	    MAX_TESTS=34
	    ;;
	2.4.6 )
	    MAX_TESTS=600
	    ;;
	2.5.6 )
	    MAX_TESTS=600
	    ;;
	2.6.9 )
	    MAX_TESTS=1300
	    ;;
	* )
	     MAX_TESTS=800
	     ;;
    esac

    actual_versions="$actual_versions $VERSION"

    if ! pyenv local $VERSION ; then
	rc=1
	mailbody_line="pyenv local $VERSION not installed"
	echo $mailbody_line >> $MAILBODY
    else
      echo Python Version $(pyenv local) > $LOGFILE
      echo "" >> $LOGFILE
      typeset -i ALL_FILES_STARTTIME=$(date +%s)
      cmd="python ./${MAIN} --max ${MAX_TESTS} --syntax-verify --$VERSION"
      echo "$cmd" >>$LOGFILE 2>&1
      $cmd >>$LOGFILE 2>&1
      rc=$?

      echo Python Version $(pyenv local) >> $LOGFILE
      echo "" >>$LOGFILE

      typeset -i ALL_FILES_ENDTIME=$(date +%s)
      (( time_diff =  ALL_FILES_ENDTIME - ALL_FILES_STARTTIME))
      time_str=$(displaytime $time_diff)
      echo ${time_str}. >> $LOGFILE
    fi

    SUBJECT_PREFIX="$WHAT (max $MAX_TESTS) for"
    if ((rc == 0)); then
	mailbody_line="Python $VERSION ok; ${time_str}."
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION ok" ${USER}@localhost
    else
	mailbody_line="Python $VERSION failed; ${time_str}."
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" ${USER}@localhost
	tail -v $LOGFILE | mail -s "$HOST $SUBJECT_PREFIX $VERSION not ok" ${EMAIL}
    fi
    echo $mailbody_line >> $MAILBODY
    rm .python-version
done

typeset -i RUN_ENDTIME=$(date +%s)
(( time_diff =  RUN_ENDTIME - RUN_STARTTIME))
elapsed_time=$(displaytime $time_diff)
echo "${WHAT} complete; ${elapsed_time}." >> $MAILBODY
cat $MAILBODY | mail -s "$HOST $WHAT ${elapsed_time}." ${EMAIL}
