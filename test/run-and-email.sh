#!/usr/bin/bash
EMAIL=${EMAIL:-rb@dustyfeet.com}
for VERSION in 2.7.14 2.6.9 ; do
    LOGFILE=/tmp/pyenlib-$VERSION-$$.log
    python ./test_pyenvlib.py --max 800 --weak-verify --$VERSION  >$LOGFILE 2>&1
    rc=$?
    if ((rc == 0)); then
	tail -v $LOGFILE | mail -s \""$VERSION ok"\" rocky@localhost
    else
	tail -v $LOGFILE | mail -s \""$VERSION not ok"\" rocky@localhost
	tail -v $LOGFILE | mail -s \""$VERSION not ok"\" rb@dustyfeet.com
    fi
done
