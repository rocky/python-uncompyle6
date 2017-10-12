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
if ! source ./setup-master.sh ; then
    exit $?
fi

cd ..
source $PACKAGE/version.py
echo $VERSION

for pyversion in $PYVERSIONS; do
    # Pick out first two numbers
    first_two=$(echo $pyversion | cut -d'.' -f 1-2 | sed -e 's/\.//')
    rm -fr build
    python setup.py bdist_egg bdist_wheel
    mv -v dist/uncompyle6-$VERSION-{py2.py3,py$first_two}-none-any.whl
done

python ./setup.py sdist
