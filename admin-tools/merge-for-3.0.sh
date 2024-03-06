#/bin/bash
uncompyle6_merge_30_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})
if . ./setup-python-3.0.sh; then
    git merge python-3.3-to-3.5
fi
cd $uncompyle6_merge_30_owd
