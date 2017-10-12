#!/bin/bash
PACKAGE=uncompyle6
if ! source ./setup-python-2.4.sh ; then
    exit $?
fi
source $PACKAGE/version.py
echo $VERSION
PYVERSIONS='2.4.6 2.5.6'
for pyversion in $PYVERSIONS; do
    # Pick out first two numbers
    first_two=$(echo $pyversion | cut -d'.' -f 1-2 | sed -e 's/\.//')
    rm -fr build
    python setup.py bdist_egg
done
tarball=dist/uncompyle6-$VERSION-tar.gz
if -f $tarball; then
    rm dist/uncompyle6-$VERSION-tar.gz
fi
