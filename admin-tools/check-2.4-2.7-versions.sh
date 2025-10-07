#!/bin/bash
# Run tests over all Python versions in branch python-2.4-2.7
set -e
function finish {
  cd $uncompyle6_check_owd
}
uncompyle6_check_owd=$(pwd)
trap finish EXIT

cd $(dirname ${BASH_SOURCE[0]})
if ! source ./pyenv-2.4-2.7-versions ; then
    exit $?
fi
if ! source ./setup-python-2.4.sh ; then
    exit $rc
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
