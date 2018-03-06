#!/bin/bash
# Runs test_pyenvlib.test on all versions of Python master.
function finish {
  cd $owd
}

# FIXME put some of the below in a common routine
owd=$(pwd)
trap finish EXIT

cd $(dirname ${BASH_SOURCE[0]})
if ! source ./pyenv-newer-versions ; then
    exit $?
fi
if ! source ./setup-master.sh ; then
    exit $?
fi
cd ../test
for version in $PYVERSIONS; do
    if ! pyenv local $version ; then
	exit $?
    fi
    echo "====== Running test_pyenvlib.py on $version ====="
    if ! python ./test_pyenvlib.py --weak-verify --max 800 --${version} ; then
	exit $?
    fi
    echo "------ Done test_pyenvlib.py on $version -----"
done
