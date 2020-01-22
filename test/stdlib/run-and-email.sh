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

. ../../admin-tools/pyenv-newer-versions

USER=${USER:-rocky}
EMAIL=${EMAIL:-rb@dustyfeet.com}
SUBJECT_PREFIX="stdlib unit testing for"

typeset -i RUN_STARTTIME=$(date +%s)

actual_versions=""
DEBUG=""  # -x

for VERSION in $PYVERSIONS ; do
    typeset -i rc=0
    LOGFILE=/tmp/runtests-$VERSION-$$.log

    case "$VERSION" in
	3.0.1 | 3.1.5 | 3.2.6 | 3.8.1 )
	    continue
	    ;;
    esac
    actual_versions="$actual_versions $VERSION"

    if ! pyenv local $VERSION ; then
	rc=1
    else
      STOP_ONERROR=1 /bin/bash $DEBUG ./runtests.sh  >$LOGFILE 2>&1
      rc=$?
    fi
    SUBJECT_PREFIX="runtests verify for"
    if ((rc == 0)); then
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION ok" ${USER}@localhost
    else
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" ${USER}@localhost
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" $EMAIL
    fi
done

typeset -i RUN_ENDTIME=$(date +%s)
(( time_diff =  RUN_ENDTIME - RUN_STARTTIME))
elapsed_time=$(displaytime $time_diff)
echo "Run complete $elapsed_time for versions $actual_versions" | mail -s "runtests in $elapsed_time" ${EMAIL}
