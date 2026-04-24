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

rm -fr build
for pyversion in $PYVERSIONS; do
    echo --- $pyversion ---
    if [[ ${pyversion:0:4} == "pypy" ]] ; then
	echo "$pyversion - PyPy does not get special packaging"
	continue
    elif [[ ${pyversion:0:4} == "graa" ]] ; then
	echo "$pyversion - Graal does not get special packaging"
	continue
    fi
    if ! pyenv local $pyversion ; then
	exit $?
    fi
    # pip bdist_egg create too-general wheels. So
    # we narrow that by moving the generated wheel.

    # Pick out first two number of version, e.g. 3.5.1 -> 35
    first_two=$(echo $pyversion | cut -d'.' -f 1-2 | sed -e 's/\.//')
    rm -fr build
    pip wheel --wheel-dir=dist -e .
    mv -v dist/${PACKAGE}-${__version__}-{py3,py$first_two}-none-any.whl
done

python -m build --sdist
finish
