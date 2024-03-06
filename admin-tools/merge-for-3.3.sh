#/bin/bash
uncompyle6_merge_33_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})
if . ./setup-python-3.3.sh; then
    git merge master
fi
cd $uncompyle6_merge_33_owd
