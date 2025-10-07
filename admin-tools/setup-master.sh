#!/bin/bash
# Check out master branch and dependent development master branches
PYTHON_VERSION=3.13

bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

uncompyle6_owd=$(pwd)
mydir=$(dirname $bs)
fulldir=$(readlink -f $mydir)
cd $mydir
. ./checkout_common.sh
cd $fulldir/..
(cd $fulldir/.. && \
     setup_version python-spark master && \
     setup_version python-xdis master )
checkout_finish master
