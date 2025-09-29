#!/bin/bash
PACKAGE=uncompyle6

# FIXME put some of the below in a common routine
function finish {
  if [[ -n "$make_uncompyle6_newest_owd" ]] then
     cd $make_uncompyle6_newest_owd
  fi
}

cd $(dirname ${BASH_SOURCE[0]})
make_uncompyle6_newest_owd=$(pwd)
trap finish EXIT

if ! source ./pyenv-newest-versions ; then
    exit $?
fi
if ! source ./setup-master.sh ; then
    exit $?
fi

cd ..
source $PACKAGE/version.py
echo $__version__

# Python 3.12 and 3.13 are more restrictive in packaging
pyenv local 3.11

rm -fr build
pip wheel --wheel-dir=dist .
python -m build --sdist
finish
