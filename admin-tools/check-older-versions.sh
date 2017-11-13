#!/bin/bash
function finish {
  cd $owd
}
owd=$(pwd)
trap finish EXIT

cd $(dirname ${BASH_SOURCE[0]})
if ! source ./pyenv-older-versions ; then
    exit $?
fi
if ! source ./setup-python-2.4.sh ; then
    exit $?
fi

PYVERSIONS='2.7.14 2.6.9 3.3.6 3.4.2 3.5.4 3.6.3'

cd ..
for version in $PYVERSIONS; do
    if ! pyenv local $version ; then
	exit $?
    fi
    make clean && python setup.py develop
    if ! make check ; then
	exit $?
    fi
done
