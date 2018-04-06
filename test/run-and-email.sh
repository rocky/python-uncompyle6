#!/bin/bash

function displaytime {
    printf "ran in "
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

PYVERSION=${PYVERSION:-"3.5.5 2.7.14 3.2.6 3.3.7 3.4.8 2.6.9 3.6.4"}
# PYVERSION=${PYVERSION:-"3.5.5"}

USER=${USER:-rocky}
EMAIL=${EMAIL:-rb@dustyfeet.com}
MAX_TESTS=${MAX_TESTS:-800}
typeset -i RUN_STARTTIME=$(date +%s)

for VERSION in $PYVERSION ; do
    typeset -i rc=0
    LOGFILE=/tmp/pyenvlib-$VERSION-$$.log

    if [[ $VERSION == '3.5.5' ]] ; then
	MAX_TESTS=224
    elif [[ $VERSION == '3.2.6' ]] ; then
	MAX_TESTS=700
    elif [[ $VERSION == '3.6.4' ]] ; then
	MAX_TESTS=400
    else
	MAX_TESTS=800
    fi

    if ! pyenv local $VERSION ; then
	rc=1
    else
      echo Python Version $(pyenv local) > $LOGFILE
      echo "" >> $LOGFILE
      typeset -i ALL_FILES_STARTTIME=$(date +%s)
      python ./test_pyenvlib.py --max ${MAX_TESTS} --weak-verify --$VERSION  >>$LOGFILE 2>&1
      rc=$?

      echo Python Version $(pyenv local) >> $LOGFILE
      echo "" >>$LOGFILE

      typeset -i ALL_FILES_ENDTIME=$(date +%s)
      (( time_diff =  ALL_FILES_ENDTIME - ALL_FILES_STARTTIME))
      displaytime $time_diff >> $LOGFILE
    fi

    SUBJECT_PREFIX="pyenv weak verify (max $MAX_TESTS) for"
    if ((rc == 0)); then
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION ok" ${USER}@localhost
    else
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" ${USER}@localhost
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" ${EMAIL}
    fi
    rm .python-version
done

typeset -i RUN_ENDTIME=$(date +%s)
(( time_diff =  RUN_ENDTIME - RUN_STARTTIME))
elapsed_time=$(displaytime $time_diff)
echo "Run complete $elapsed_time for versions $PYVERSION" | mail -s "pyenv weak verify in $elapsed_time" ${EMAIL}
