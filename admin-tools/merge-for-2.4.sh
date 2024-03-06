#/bin/bash
uncompyle6_merge_24_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})
if . ./setup-python-2.4.sh; then
    git merge python-3.0-to-3.2
fi
cd $uncompyle6_merge_24_owd
