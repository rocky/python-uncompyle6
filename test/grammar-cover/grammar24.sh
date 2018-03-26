#!/bin/bash
# Remake Python 2.4 grammar statistics
VERS=24
me=${BASH_SOURCE[0]}
workdir=$(dirname $me)
cd $workdir
workdir=$(pwd)
tmpdir=$workdir/../../tmp/grammar-cover
[[ -d  $tmpdir ]] || mkdir $tmpdir
cd $workdir/../..
source ./admin-tools/setup-python-2.4.sh
GRAMMAR_TXT=$tmpdir/grammar-${VERS}.txt
pyenv local 2.4.6
cd ./test
if [[ -r $GRAMMAR_TXT ]]; then
    GRAMMAR_SAVE_TXT=${tmpdir}/grammar-${VERS}-save.txt
    cp $GRAMMAR_TXT $GRAMMAR_SAVE_TXT
fi
make grammar-coverage-2.4 && \
    spark-parser-coverage --path ${tmpdir}/spark-grammar-${VERS}.cover > $GRAMMAR_TXT
