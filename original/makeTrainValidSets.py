'''
Create train and test sets (lists) when given a word.

Find all tarfiles
Extract each .txt file
Read in each file of labels
Check for label in labels
Decide if given item goes in train or valid
Store filename (path, etc) in train or valid
close and delete folders
Next
'''

import sys, os
import tarfile
import string
import shutil
from random import shuffle

stopList = ['at', 'the', 'it', 'them', 'a', 'an', 'is', 'has', 'and', 'that']

'''
Find train and validation lists
'''
def find_train_and_validation(directories, label):
    #keep track of what tarfiles have which labels in them
    hasLabelList = {}
    unknownLabelList = {}
    noLabelList = {}
    #we need to accumulate the labels for each tarfile, not each file (individual)?
    #find all tarfiles: and all label files in them
    fileList = {}#find_tared_data('.')
    for directory in directories:
        fileList.update(find_tared_data(directory))
    print "FileList: ",len(fileList)
    # 
    #for each tarfile in the list
    for tarfilename in fileList.keys():
        print "Processing ",tarfilename
        #open the tarfile
        tared = tarfile.open(tarfilename, 'r')
        #create dictionary
        dictionary_this_file = {}
        try:
            #for each label file in the tarfile
            for index in range(0, len(fileList[tarfilename])):
                #read all the labels into the same dictionary
                #extract the label files
                tared.extractall(members=current_file(tared, fileList[tarfilename][index]))
                #load labels into the dictionary
                load_labels(fileList[tarfilename][index], dictionary_this_file)
            #have all labels from tarfile in the dictionary: check if needed label there?
            if label in dictionary_this_file.keys():
                if dictionary_this_file[label]>0:
                    #add this tarfile and its list to hasLabelList
                    hasLabelList[tarfilename] = fileList[tarfilename]
                else:
                    #add this to the noLabelList: (not red, etc)
                    noLabelList[tarfilename] = fileList[tarfilename]
            else:
                #label not present: unknown labeling:
                #add the tarfile and list to unknownLabelList
                unknownLabelList[tarfilename] = fileList[tarfilename]
        finally:
            #remove extracted directory
            dirToDel = fileList[tarfilename][index].split('/')[0]
            shutil.rmtree(dirToDel)#be careful here
        #close tarfile
        tared.close()
    #here, we have three dictionaries: positive, negative, and unknown, containing tarfiles
    split_data(label, hasLabelList, noLabelList, unknownLabelList)

'''
Function: split the data we have into several train and valid sets
'''
def split_data(label, positives, negatives, unknowns):
    print "What are we working with: ",len(positives), ',', len(negatives),',',len(unknowns)
    #split into several sets: 
    #create a folder label_sets
    if not os.path.exists("TrainingSets/"+label): 
        os.makedirs("TrainingSets/"+label)
    # in folder create several numbered files: train1 valid1; train2 valid2; etc
    # rules: always need at least one positive example of the label in the train set, and one in valid
    # rule if we only have one folder, split it so some are in train, some in test
    # others: random (and split 4-1)
    #for each possible arrangement: create a pair of files and save
    for i,item in enumerate(positives):
        #train and valid lists
        trainList = []
        validList = []
        #add item to positives, then add others
        validList.append((item,positives[item]))
        for other in positives:
            #check that it isn't our left out
            if other != item:
                #add item
                trainList.append((other,positives[other]))
        lenNegatives = (len(negatives)+1)/5
        lenUnknowns = (len(unknowns)+1)/5
        #shuffle the stuff
        negativeList = negatives.keys()
        unknownList= unknowns.keys()
        shuffle(negativeList)
        shuffle(unknownList)
        print "How many ",lenNegatives,',',lenUnknowns
        #shuffle(negatives)
        #shuffle(unknowns)
        #put some into train and test
        for j in range(0, lenNegatives):
            validList.append((negativeList[j], negatives[negativeList[j]]))
        for j in range(0, lenUnknowns):
            validList.append((unknownList[j],unknowns[unknownList[j]]))
        for j in range(lenNegatives, len(negatives)):
            trainList.append((negativeList[j],negatives[negativeList[j]]))
        for j in range(lenUnknowns, len(unknowns)):
            trainList.append((unknownList[j],unknowns[unknownList[j]]))
        #this should be all of them
        assert (len(unknowns) + len(negatives) + len(positives)) == (len(trainList) + len(validList)), " Haven't used all of the items "
        print "Train and test sets: ",len(trainList),',',len(validList)
        #store the result in files 
        f = open("TrainingSets/"+label+'/train_'+label+'_'+str(i),'w')
        for traintarfile, trainfilelist in trainList:
            for filename in trainfilelist:
                f.write(traintarfile+' '+filename+'\n')
        f.close()
        #store validation names
        f = open("TrainingSets/"+label+'/valid_'+label+'_'+str(i),'w')
        for validtarfile, validfilelist in validList:
            for filename in validfilelist:
                f.write(validtarfile+' '+filename+'\n')
        f.close()
    #if directory exists, assume sets already exist, and skip

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
            #print "Processing file... "
            #print item,',',dirs
            #if it really is a tar file:
            if tarfile.is_tarfile(os.path.join(dirs,item)):#do we need path too? yes
                tared = tarfile.open(os.path.join(dirs,item), 'r')
                contents = tared.getnames()
                key = os.path.join(dirs, item)
                print "adding Key: ",key
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
Load the positive and negative labels
'''
def load_labels(filename, dictionary):
    if not os.path.exists(filename+".txt"):
        print "WARNING: No label file."
        return
    try:
        f = open(filename+".txt")#default read
    except IOError:
        print "Error loading sentences...", sys.exc_info()[0]
        print "Could not load ", filename+".txt"
        #raw_input('-Enter-')
        sys.exit()
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
        #raw_input('-Enter-')
        sys.exit()
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
                        dictionary[word] = dictionary[word] - 1
                    else:
                        dictionary[word] = 0
        f.close()

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
    print type(sys.argv),',',type(sys.argv[0])
    if len(sys.argv) < 2:
        print "Need an argument"
        sys.exit()
    #add possible many labels
    label = sys.argv[1]
    print "Using: ",label
    #create folder for datsets if it isn't already here
    if not os.path.exists("TrainingSets"): 
        os.makedirs("TrainingSets")
    #find crop values from masks
    directories = ['tared', 'lab']
    find_train_and_validation(directories, label)
    print "Ending in Main..."
    sys.exit()