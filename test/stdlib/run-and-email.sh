#!/bin/bash
USER=${USER:-rocky}
EMAIL=${EMAIL:-rb@dustyfeet.com}
SUBJECT_PREFIX="stdlib unit testing for"
for VERSION in 2.6.9 2.7.17 3.4.10 3.5.9 3.6.9 ; do
    typeset -i rc=0
    LOGFILE=/tmp/runtests-$VERSION-$$.log
    if ! pyenv local $VERSION ; then
	rc=1
    else
      /bin/bash ./runtests.sh  >$LOGFILE 2>&1
      rc=$?
    fi
    if ((rc == 0)); then
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION ok" ${USER}@localhost
    else
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" ${USER}@localhost
	tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX $VERSION not ok" $EMAIL
    fi
done
