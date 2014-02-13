'''
Create a compilation of all labels in this tarfile: add it to the tarfile
NOT TESTED
'''

import sys, os
import tarfile
import numpy as np
import cv,cv2
import shutil
import string

stopList = ['at', 'the', 'it', 'them', 'a', 'an', 'is', 'has', 'and', 'that']

def find_labels(directories = []):
    #find tar files
    #find files in tar files
    fileList = find_tared_data('.')
    for directory in directories:
        fileList.update(find_tared_data(directory))
    #for each tarfile in the list
    for tarfilename in fileList.keys():
        #open the tarfile
        tared = tarfile.open(tarfilename, 'r')
        #create dictionary
        dictionary_this_file = {}
        #for each label file in the tarfile
        for index in range(0, len(fileList[tarfilename])):
            #read all the labels into the same dictionary
            #extract the label files
            tared.extractall(members=current_file(tared, fileList[tarfilename][index]))
            #load labels into the dictionary
            load_labels(fileList[tarfilename][index], dictionary_this_file)
        #have all labels for this tarfile: print them to a file, add to tar
        f = open(tarfilename[:-4]+".txt")
        f.write(str(len(dictionary_this_file))+"\n")
        for key in dictionary_this_file.keys():
            f.write(key+' '+str(dictionary_this_file[key])+'\n')
        f.close()
        #add file to tar
        tared.add(tarfilename[:-4]+".txt")
        #close tarfile
        tared.close()

    #cv.Save("meanImage",sum_image) #cv.Load to get it back correctly
    #save the dictionary too: length followed by each word
    f = open("dictionaryAll.txt", 'w')
    f.write(str(len(labels.keys()))+'\n')
    for key in labels.keys():
        f.write(key+'\n')
    f.close()
    
def load_labels(filename, dictionary):
    if not os.path.exists(filename+".txt"):
        print "WARNING: No label file."
        return
    try:
        f = open(filename+".txt")#default read
    except IOError:
        print "Error loading sentences...", sys.exc_info()[0]
        print "Could not load ", filename+".txt"
        raw_input('-Enter-')
    else:
        #get all sentences (one per line)
        sentences = f.readlines() #read sentences
        #while still sentences in list:
        for line in sentences:
            #parse sentences
            words = line.split() #split on whitespace, no empties
            #store words
            for word in words:
                exclude = set(string.punctuation)
                word = ''.join(c.lower() for c in word if c not in exclude)
                if word not in stopList:
                    #store counts
                    if word in dictionary:
                        dictionary[word] = dictionary[word] + 1
                    else:
                        dictionary[word] = 1
        f.close()
    try:
        f = open(filename+"_Not.txt")#default read
    except IOError:
        print "Error loading sentences...", sys.exc_info()[0]
        print "Could not load ", filename+"_Not.txt"
        raw_input('-Enter-')
    else:
        #get all sentences (one per line)
        sentences = f.readlines() #read sentences
        #while still sentences in list:
        for line in sentences:
            #parse sentences
            words = line.split() #split on whitespace, no empties
            #store words
            for word in words:
                exclude = set(string.punctuation)
                word = ''.join(c.lower() for c in word if c not in exclude)
                if word not in stopList:
                    #store counts
                    if word in dictionary:
                        dictionary[word] = dictionary[word] + 1
                    else:
                        dictionary[word] = 1
        f.close()

'''
Function: find all image files recursively in directory "data"
    *collect the list of tar files & list of files in each tar*This way we don't have to extract them, just each image as we need it...
'''
def find_tared_data(directory='original/tared'):
    print "Finding Data ",directory
    #check color and real vs generated
    #check directoryList not emtpy
    files = {} #store the path up to the tar (.../.../...tar), and have its value be the list of files in the tar
    for dirs, subDirs, filenames in os.walk(directory):#check walks correct location 
        #we expect these to be tar files now, we want to look inside
        for item in filenames:
            print "Processing file... "
            #print item,',',dirs
            #if it really is a tar file:
            if tarfile.is_tarfile(os.path.join(dirs,item)):#do we need path too? yes
                tared = tarfile.open(os.path.join(dirs,item), 'r')
                contents = tared.getnames()
                key = os.path.join(dirs, item)
                #print "Key: ",key
                #print "Filtered Contents: "
                for pic in contents:
                    #print "Contents: ",type(pic),", ",pic
                    #check if pic is the original color picture (not crop, not mask etc)
                    if not ("_loc" in pic) and not ("_crop" in pic) and not ("_Not" in pic) and ('.txt' in pic):
                        #print "File: ",type(pic),", ",pic
                        #emergency_quit()
                        if key in files:
                            checklength = len(files[key])
                            files[key].append(pic[:-4])
                            assert checklength!=len(files[key]), "Failed to add item to list: check reference stuff"
                        else:
                            files[key] = []
                            files[key].append(pic[:-4])
                #clear for next file...shouldn't be needed now that I look
                #members[:] = []
                tared.close()
    #return to previous Directory
    return files

'''
Function: tries to load only needed file at once...
'''
def current_file(members, filename):
    for tarinfo in members:
        if tarinfo.name == filename+"_Not.txt" or tarinfo.name == filename+".txt":
            yield tarinfo

    '''
Function: DEBUG: escape early if we see something bad
'''
def emergency_quit():
    s = raw_input('--> ')
    if s=='q':
        sys.exit()

if __name__ == "__main__":
    #find crop values from masks
    directories = ['tared', 'lab']
    find_labels(directories)
    print "Ending in Main..."
    sys.exit()