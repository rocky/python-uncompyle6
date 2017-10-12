#!/bin/bash
PACKAGE=uncompyle6

# FIXME put some of the below in a common routine
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

<<<<<<< HEAD
cd ..
source $PACKAGE/version.py
=======
source ../$PACKAGE/version.py
>>>>>>> master
echo $VERSION

for pyversion in $PYVERSIONS; do
    if ! pyenv local $pyversion ; then
	exit $?
    fi

    rm -fr build
    python setup.py bdist_egg
done

# Pypi can only have one source tarball.
# Tarballs can get created from the above setup, so make sure to remove them since we want
# the tarball from master.

tarball=dist/uncompyle6-$VERSION-tar.gz
<<<<<<< HEAD
if [[ -f $tarball ]]; then
=======
if -f $tarball; then
>>>>>>> master
    rm -v dist/uncompyle6-$VERSION-tar.gz
fi
