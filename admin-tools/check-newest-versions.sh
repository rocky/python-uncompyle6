#!/bin/bash
function finish {
  cd $uncompyle6_check_owd
}

# FIXME put some of the below in a common routine
uncompyle6_check_owd=$(pwd)
trap finish EXIT

cd $(dirname ${BASH_SOURCE[0]})
if ! source ./pyenv-newest-versions ; then
    exit $?
fi
if ! source ./setup-master.sh ; then
    exit $?
fi
cd ..
for version in $PYVERSIONS; do
    echo --- $version ---
    if ! pyenv local $version ; then
	exit $?
    fi
    make clean && pip install -e .
    if ! make check-short; then
	exit $?
    fi
    echo === $version ===
done
make check
