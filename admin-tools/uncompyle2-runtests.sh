#!/bin/bash
# Use pycdc to run our test/bytecode_2.7* test suite
bs=${BASH_SOURCE[0]}
topdir=$(dirname $bs)/..
(cd $topdir && pyenv local 2.7.14)
testdir=$topdir/test
fulldir=$(readlink -f $testdir)
cd $fulldir

for bytecode in bytecode_2.7/*.pyc ; do
    echo $bytecode
    uncompyle2 $bytecode > /dev/null
    echo ================ $bytecode rc: $? ==============
done

tmpdir=/tmp/test-2.7
( cd bytecode_2.7_run &&
      mkdir $tmpdir || true
      for bytecode in *.pyc ; do
	  shortname=$(basename $bytecode .pyc)
	  echo $bytecode
	  py_file=${tmpdir}/${shortname}.py
	  typeset -i rc=0
	  uncompyle2 $bytecode > $py_file
	  rc=$?
	  if (( rc == 0 )); then
	      python $py_file
	      rc=$?
	  fi
	  echo ================ $bytecode rc: $rc ==============
      done
)
