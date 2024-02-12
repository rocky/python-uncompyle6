#!/bin/bash
# Check out python-2.4-to-2.7 and dependent development branches.

set -e
PYTHON_VERSION=2.4.6

bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

function checkout_version {
    local repo=$1
    version=${2:-python-2.4-to-2.7}
    echo Checking out $version on $repo ...
    (cd ../$repo && git checkout $version && pyenv local $PYTHON_VERSION) && \
	git pull
    return $?
}

function finish {
  cd $owd
}
owd=$(pwd)
trap finish EXIT

export PATH=$HOME/.pyenv/bin/pyenv:$PATH

mydir=$(dirname $bs)
fulldir=$(readlink -f $mydir)
(cd $fulldir/.. && checkout_version python-spark && checkout_version python-xdis python-2.4-to-2.7 &&
     checkout_version python-uncompyle6)

git pull
rm -v */.python-version || true
finish
