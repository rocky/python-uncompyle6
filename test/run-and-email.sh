#!/bin/bash
USER=${USER:-rocky}
EMAIL=${EMAIL:-rb@dustyfeet.com}
MAX_TESTS=${MAX_TESTS:-800}
for VERSION in 2.7.14 2.6.9 ; do
    typeset -i rc=0
    LOGFILE=/tmp/pyenlib-$VERSION-$$.log
    if ! pyenv local $VERSION ; then
	rc=1
    else
      python ./test_pyenvlib.py --max ${MAX_TESTS} --weak-verify --$VERSION  >$LOGFILE 2>&1
      rc=$?
    fi
    if ((rc == 0)); then
	tail -v $LOGFILE | mail -s \""$VERSION ok"\" ${USER}@localhost
    else
	tail -v $LOGFILE | mail -s \""$VERSION not ok"\" ${USER}@localhost
	tail -v $LOGFILE | mail -s \""$VERSION not ok"\" ${EMAIL}
    fi
done
