#!/bin/bash
PYTHON_VERSION=2.4.6

owd=$(pwd)
bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi
mydir=$(dirname $bs)
fulldir=$(readlink -f $mydir)
cd $fulldir/..
(cd ../python-spark && git checkout python-2.4 && pyenv local $PYTHON_VERSION) && git pull && \
    (cd ../python-xdis && git checkout python-2.4 && pyenv local $PYTHON_VERSION) && git pull && \
    git checkout python-2.4 &&  pyenv local $PYTHON_VERSION && git pull
cd $owd
