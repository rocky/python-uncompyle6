#!/bin/bash
PACKAGE=uncompyle6

# FIXME put some of the below in a common routine
function finish {
  cd $owd
}
owd=$(pwd)
trap finish EXIT

cd $(dirname ${BASH_SOURCE[0]})
if ! source ./pyenv-2.4-2.7-versions ; then
    exit $?
fi
if ! source ./setup-python-2.4.sh ; then
    exit $?
fi

cd ..
source $PACKAGE/version.py
echo $__version__

for pyversion in $PYVERSIONS; do
    if ! pyenv local $pyversion ; then
	exit $?
    fi

    rm -fr build
    python setup.py bdist_egg
done

pyenv local 2.7.18
python setup.py bdist_wheel
mv -v dist/${PACKAGE}-$__version__-py2{.py3,}-none-any.whl

# Pypi can only have one source tarball.
# Tarballs can get created from the above setup, so make sure to remove them since we want
# the tarball from master.

tarball=dist/${PACKAGE}-${__version_}_-tar.gz
if [[ -f $tarball ]]; then
    rm -v dist/${PACKAGE}-${__version__}-tar.gz
fi
