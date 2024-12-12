#/bin/bash
uncompyle6_merge_36_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})
if . ./setup-python-3.6.sh; then
    git merge master
fi
cd $uncompyle6_merge_36_owd
