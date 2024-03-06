#!/bin/bash
# Run tests over all Python versions in branch python-3.0-3.2
set -e
function finish {
  cd $owd
}

owd=$(pwd)
trap finish EXIT

cd $(dirname ${BASH_SOURCE[0]})
if ! source ./pyenv-3.0-3.2-versions ; then
    exit $?
fi
if ! source ./setup-python-3.0.sh ; then
    exit $?
fi

cd ..
for version in $PYVERSIONS; do
    echo --- $version ---
    if ! pyenv local $version ; then
	exit $?
    fi
    make clean && python setup.py develop
    if ! make check ; then
	exit $?
    fi
    echo === $version ===
done
finish
