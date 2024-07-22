#!/bin/bash
# Check out python-3.3-to-3.5 and dependent development branches.
PYTHON_VERSION=3.3.7

bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

mydir=$(dirname $bs)
. ./checkout_common.sh
fulldir=$(readlink -f $mydir)
cd $fulldir/..
(cd $fulldir/.. && \
     setup_version python-spark master && \
     setup_version python-xdis python-3.3 )

checkout_finish python-3.3-to-3.5
