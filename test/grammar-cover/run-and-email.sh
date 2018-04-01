#!/bin/bash
USER=${USER:-rocky}
EMAIL=${EMAIL:-rb@dustyfeet.com}
SUBJECT_PREFIX="grammar cover testing for"
LOGFILE=/tmp/grammar-cover-$$.log
/bin/bash ./grammar-all.sh  >$LOGFILE 2>&1
rc=$?
if ((rc == 0)); then
    tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX ok" ${USER}@localhost
else
    tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX not ok" ${USER}@localhost
    tail -v $LOGFILE | mail -s "$SUBJECT_PREFIX not ok" $EMAIL
fi
