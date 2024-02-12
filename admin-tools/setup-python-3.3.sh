#!/bin/bash
# Check out python-3.3-to-3.5 and dependent development branches.
set -e
PYTHON_VERSION=3.3.7

bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

# FIXME put some of the below in a common routine
function checkout_version {
    local repo=$1
    version=${2:-python-3.3-to-3.5}
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

fulldir=$(readlink -f $mydir)
cd $fulldir/..
(cd $fulldir/.. && checkout_version python-spark master && checkout_version python-xdis &&
     checkout_version python-uncompyle6)
rm -v */.python-version || true

git pull
rm -v */.python-version || true
finish
