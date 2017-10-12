#!/bin/bash
PACKAGE=uncompyle6
source $PACKAGE/version.py
. ./setup-master.sh
echo $VERSION
PYVERSIONS='3.5.2 3.6.2 2.6.9 3.3.6 2.7.13 3.4.2 3.5.6'
for pyversion in $PYVERSIONS; do
    # Pick out first two numbers
    first_two=$(echo $pyversion | cut -d'.' -f 1-2 | sed -e 's/\.//')
    python setup.py bdist_egg bdist_wheel
    mv -v dist/uncompyle6-$VERSION-{py2.py3,py$first_two}-none-any.whl
done

python ./setup.py sdist
