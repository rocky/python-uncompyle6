#!/bin/bash
PACKAGE=uncompyle6

# FIXME put some of the below in a common routine
function finish {
  cd $owd
}

cd $(dirname ${BASH_SOURCE[0]})
if ! source ./pyenv-older-versions ; then
    exit $?
fi
if ! source ./setup-python-2.4.sh ; then
    exit $?
fi

source ../$PACKAGE/version.py
echo $VERSION

for pyversion in $PYVERSIONS; do
    # Pick out first two numbers
    first_two=$(echo $pyversion | cut -d'.' -f 1-2 | sed -e 's/\.//')
    rm -fr build
    python setup.py bdist_egg
done

# Pypi can only have one source taball.
# Tarballs can get created from the above setup, so make sure to remove them since we want
# the tarball from master.

tarball=dist/uncompyle6-$VERSION-tar.gz
if -f $tarball; then
    rm -v dist/uncompyle6-$VERSION-tar.gz
fi
