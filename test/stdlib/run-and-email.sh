#!/bin/bash
EMAIL=${EMAIL:-rb@dustyfeet.com}
for VERSION in 2.7.14 2.6.9 ; do
    typeset -i rc=0
    LOGFILE=/tmp/runtests-$VERSION-$$.log
    if ! pyenv local $VERSION ; then
	rc=1
    else
      ./runtests.sh  >$LOGFILE 2>&1
      rc=$?
    fi
    rc=$?
    if ((rc == 0)); then
	tail -v $LOGFILE | mail -s \""$VERSION ok"\" rocky@localhost
    else
	tail -v $LOGFILE | mail -s \""$VERSION not ok"\" rocky@localhost
	tail -v $LOGFILE | mail -s \""$VERSION not ok"\" rb@dustyfeet.com
    fi
done
