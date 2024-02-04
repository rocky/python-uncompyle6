#!/bin/bash
# Checks xpython passes all runnable bytecode here

for dir in bytecode_*_run; do
    for file in ${dir}/*.pyc; do
	echo $file
	if ! xpython $file; then
	    break
	fi
    done
done
