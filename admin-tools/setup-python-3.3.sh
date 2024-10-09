#!/bin/bash
# Check out python-3.3-to-3.5 and dependent development branches.
bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

PYTHON_VERSION=3.3

uncompyle6_owd=$(pwd)
mydir=$(dirname $bs)
cd $mydir
fulldir=$(readlink -f $mydir)
. ./checkout_common.sh
cd $fulldir/..
(cd $fulldir/.. && \
     setup_version python-spark python-3.3 && \
     setup_version python-xdis python-3.3 )

checkout_finish python-3.3-to-3.5
