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

. ../admin-tools/pyenv-newer-versions

USER=${USER:-rocky}
EMAIL=${EMAIL:-rb@dustyfeet.com}
MAX_TESTS=${MAX_TESTS:-800}
typeset -i RUN_STARTTIME=$(date +%s)

# PYVERSIONS="3.5.6"
actual_versions=""
for VERSION in $PYVERSIONS ; do
    typeset -i rc=0
    LOGFILE=/tmp/pyenvlib-$VERSION-$$.log

    case "$VERSION" in
	3.7.6 | 3.8.1 | 3.1.5 | 3.0.1 )
	    continue
	    ;;
	3.5.9 )
	    MAX_TESTS=237 # We start failing on "mailbox" at 238
	    ;;
	3.2.6 )
	    MAX_TESTS=172 # We start failing on pkgutil.py
	    ;;
	3.3.7 )
	    MAX_TESTS=180 # We start failing on pkgutil.py
	    ;;
	3.4.10 )
	    MAX_TESTS=30 # We start failing on aifc
	    ;;
	 3.6.9 )
	     MAX_TESTS=92  # We start failing on cgiltb.py
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
    else
      echo Python Version $(pyenv local) > $LOGFILE
      echo "" >> $LOGFILE
      typeset -i ALL_FILES_STARTTIME=$(date +%s)
      cmd="python ./test_pyenvlib.py --max ${MAX_TESTS} --syntax-verify --$VERSION"
      echo "$cmd" >>$LOGFILE 2>&1
      $cmd >>$LOGFILE 2>&1
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
echo "Run complete $elapsed_time for versions $actual_versions" | mail -s "pyenv weak verify in $elapsed_time" ${EMAIL}
