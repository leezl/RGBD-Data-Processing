#!/bin/bash

#meant to find all tars
#unpack each tar separately
#in each tar take the one .txt and _Not.txt
#copy these so there is one for each image
#retar

tarfiles=$(find . -regextype posix-extended -regex '.*[0-9]+\.tar')

#echo Tarfiles:
#echo "$tarfiles"
textExt=".txt"
pngExt=".png"

for file in $tarfiles;
do
    mkdir temp
    #untar the tar into known dir
    tar -C temp -xvf $file
    #find the numbers/ find all file name ending in .png
    filenames=$(find temp -regextype posix-extended -regex '.*_[0-9]+\.png')
    #echo Filenames:
    #echo "$filenames"
    # find single .txt not ending in loc.txt
    labelfile=$(find temp -regextype posix-extended -regex '.*[0-9]+\.txt')
    #echo Labelfile names:
    #echo "$labelfile"
    notlabelfile=$(find temp -regextype posix-extended -regex '.*[0-9]+_Not\.txt')
    #echo "$notlabelfile"
    #cp this txt into every filename replacing end with .txt and same for _Not.txt
    for filename in $filenames;
    do
	tempfilename=${filename%\.png}
	tempfilename+="_Not.txt"
        #echo "$tempfilename"
	cp $notlabelfile $tempfilename
        tempfilename=${tempfilename%_Not\.txt}
	tempfilename+=".txt"
        #echo "$tempfilename"
	cp $labelfile $tempfilename
    done
    #tar the result
    #echo ${file%\.tar}o.tar
    direc=$(echo temp/*)
    #echo ${direc#temp\/}
    tar -cvf ${file%\.tar}o.tar $direc
    rm -rf temp
done
