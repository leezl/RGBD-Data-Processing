#!/bin/bash
for i in `seq $3 $4`;
do
    echo $i
    cp $1$2\_Not.txt $1$i\_Not.txt
    cp $1$2\.txt $1$i\.txt 
done 
