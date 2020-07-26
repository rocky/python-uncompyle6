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

branch=$(cat ../../.git/HEAD | cut -d'/' -f 3)
if [[ $branch == 'python-2.4' ]]; then
    . ../../admin-tools/pyenv-older-versions
elif [[ $branch == 'master' ]]; then
    . ../../admin-tools/pyenv-newer-versions
else
    echo &1>2 "Error git branch should either be 'master' or 'python-2.4'; got: '$branch'"
    exit 1
fi

MAIN="runtests.sh"


USER=${USER:-rocky}
EMAIL=${EMAIL:-rb@dustyfeet.com}
WHAT="uncompyle6 ${MAIN}"
export BATCH=1

typeset -i RUN_STARTTIME=$(date +%s)

DEBUG=""  # -x

MAILBODY=/tmp/${MAIN}-mailbody-$$.txt

for VERSION in $PYVERSIONS ; do
    typeset -i rc=0
    LOGFILE=/tmp/runtests-$VERSION-$$.log

    case "$VERSION" in
	3.0.1 | 3.1.5 | 3.2.6 | 3.8.5 )
	    continue
	    ;;
    esac

    if ! pyenv local $VERSION ; then
	rc=1
    else
	typeset -i ALL_FILES_STARTTIME=$(date +%s)
	STOP_ONERROR=1 /bin/bash $DEBUG ./runtests.sh  >$LOGFILE 2>&1
	rc=$?

	echo Python Version $(pyenv local) >> $LOGFILE
	echo "" >>$LOGFILE
	typeset -i ALL_FILES_ENDTIME=$(date +%s)
	(( time_diff =  ALL_FILES_ENDTIME - ALL_FILES_STARTTIME))
	time_str=$(displaytime $time_diff)
	echo ${time_str}. >> $LOGFILE
    fi

    SUBJECT_PREFIX="$WHAT for"
    if ((rc == 0)); then
	mailbody_line="Python $VERSION ok; ${time_str}."
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION ok" ${USER}@localhost
    else
	mailbody_line="Python $VERSION failed; ${time_str}."
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" ${USER}@localhost
	tail -v $LOGFILE | mail -s "$HOST $SUBJECT_PREFIX $VERSION not ok" $EMAIL
    fi
    echo $mailbody_line >> $MAILBODY
done

typeset -i RUN_ENDTIME=$(date +%s)
(( time_diff =  RUN_ENDTIME - RUN_STARTTIME))
elapsed_time=$(displaytime $time_diff)
echo "${WHAT} complete; ${elapsed_time}." >> $MAILBODY
echo "Full results are in ${LOGFILE}." >> $MAILBODY
cat $MAILBODY | mail -s "$HOST $WHAT $elapsed_time" ${EMAIL}
