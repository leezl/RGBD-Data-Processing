

cropfiles=$(find $1 -regextype posix-extended -regex '.*\_crop.txt')

for file in $cropfiles;
do
    echo "$file"
    echo ${file%\.txt}o.txt
    sed 's/,/ /g' $file > ${file%\.txt}o.txt
    rename '_cropo.txt' '_crop.txt' ${file%\.txt}o.txt
done

#rename '_cropo.txt' '_crop.txt' $1*_crop.txt
