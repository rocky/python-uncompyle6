#!/bin/bash
for VERS in 2{4,5,6,7} 3{2,3,4,5} ; do
    GRAMMAR_TXT=grammar-${VERS}.txt
    spark-parser-coverage --max-count 3000 --path spark-grammar-${VERS}.cover > $GRAMMAR_TXT
done
