#!/bin/bash
cd $(dirname ${BASH_SOURCE[0]})
if ! source ./pyenv-newer-versions ; then
    exit $?
fi
if ! source ./setup-master.sh ; then
    exit $?
fi
cd ..
for version in $PYVERSIONS; do
    if ! pyenv local $version ; then
	exit $?
    fi
    make clean && python setup.py develop
    if ! make check; then
	exit $?
    fi
done
