#!/bin/bash
PYTHON_VERSION=3.7.14

function checkout_version {
    local repo=$1
    version=${2:-master}
    echo Checking out $version on $repo ...
    (cd ../$repo && git checkout $version && pyenv local $PYTHON_VERSION) && \
	git pull
    return $?
}

# FIXME put some of the below in a common routine
function finish {
  cd $owd
}

export PATH=$HOME/.pyenv/bin/pyenv:$PATH
owd=$(pwd)
bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi
mydir=$(dirname $bs)
fulldir=$(readlink -f $mydir)
cd $fulldir/..
(cd $fulldir/.. && checkout_version python-spark && checkout_version python-xdis &&
      checkout_version python-uncompyle6)
cd $owd
rm -v */.python-version >/dev/null 2>&1 || true
