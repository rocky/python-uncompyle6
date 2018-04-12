#!/bin/bash
# Use pycdc to run our test/bytecode* test suite
bs=${BASH_SOURCE[0]}
testdir=$(dirname $bs)/../test
fulldir=$(readlink -f $testdir)
cd $fulldir
for dir in bytecode_* ; do
    echo ========= $dir ================
    cd $fulldir/$dir
    for file in *.pyc; do
	if ! pycdc $file > /dev/null ; then
	    echo -----  $dir/$file ------
	fi
    done
done
