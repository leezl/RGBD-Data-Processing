'''
Python to Create the mean image, and collect all the labels

Given list of directories:
Search each for all tar files
Collect all .*[0-9].png files
Also collect all .txt files
add all images together
add all words into a dictionary
->one is object dictionary
->other is all labels dictionary
For all items
'''


import sys, os
import tarfile
import numpy as np
import cv,cv2
import shutil
import string

stopList = ['at', 'the', 'it', 'them', 'a', 'an', 'is', 'has', 'and', 'that']

def find_mean(directories = []):
    #create empty (actually value 1) image
    sum_image = np.ones((480,640,4), dtype=float)
    #create dictionary: objects
    #create dicitonary: labels
    labels = {}
    #find tar files
    #find files in tar files
    fileList = find_tared_data('.')
    for directory in directories:
        fileList = fileList + find_tared_data(directory)
    print "Files to process ",len(fileList)
    #for each file
    for index in range(0, len(fileList)):
        print "Iterating through files: ",index," of ",len(fileList)
        (path, picFile, length) = fileList[index]
        #for each file:
        print path,'\n'
        assert tarfile.is_tarfile(path), str(path)+" is not a tarfile"
        tared = tarfile.open(path, 'r')
        try:
            print "Path and file and length: ",path,',',picFile,',',length
            try:
                tared.extractall(members=current_file(tared, picFile))
                #tared.close()
                #check that the above extracted: image, depth and labels
                #load image: tar is open, just get member
                image = cv2.imread(picFile+".png", cv2.IMREAD_UNCHANGED)
                #assert image != None, "No Color Image Loaded"
                image_depth = cv2.imread(picFile+"_depth.png", cv2.IMREAD_UNCHANGED)
                #assert image_depth != None, "No Depth Image Loaded"
                if image!=None and image_depth!=None:
                    #couldnt find something we need, jsut go on to next one, else continue
                    assert image.shape[0] == image_depth.shape[0], "Wrong number of rows "+str(image.shape[0])+','+str(image_depth.shape[0])
                    assert image.shape[1] == image_depth.shape[1], "Wrong number of cols "+str(image.shape[1])+','+str(image_depth.shape[1])

                    total = np.dstack((image, image_depth.reshape(image_depth.shape[0], image_depth.shape[1], 1)))
                    assert sum_image.shape == total.shape, "Mean and image are different shapes "+str(sum_image.shape)+','+str(total.shape)

                    sum_image = sum_image + total

                    #load labels for this file too
                    print "before ",len(labels)
                    load_labels(picFile, labels) #counts negatives too...
                    print "after ",len(labels)
            finally:
                #remove extracted directory
                dirToDel = picFile.split('/')[0]
                #print dirToDel
                #emergency_quit()
                shutil.rmtree(dirToDel)#be careful here
        finally:
            #close the tar
            tared.close()
    #divide the sm
    sum_image = sum_image / len(fileList)
    #save the mean...somehow...
    test_mean_save(sum_image)
    save_image(sum_image, "meanImage.png")
    #cv.Save("meanImage",sum_image) #cv.Load to get it back correctly
    #save the dictionary too: length followed by each word
    f = open("dictionaryAll.txt", 'w')
    f.write(str(len(labels.keys()))+'\n')
    for key in labels.keys():
        f.write(key+'\n')
    f.close()

def test_mean_save(image):
    image = image.astype(np.uint16)
    save_image(image, "testMe.png")
    imageRe = cv2.imread("testMe.png", cv2.IMREAD_UNCHANGED)
    #cv.Save("meanImg", image)
    #imageRe = cv.Load("meanImg")
    print image[0,0,0], ',',imageRe[0,0,0]
    print image[0,0,3],',', imageRe[0,0,3]
    assert np.array_equal(image,imageRe), "Saving isn't correct"
    
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

def save_image(image, filename="default"):
    print "Saving Image"
    #check filename, if default add time
    if filename == "default":
        filename = filename + "_" + str(time.time()) + ".png"
    elif filename[len(filename)-4 : len(filename)] != ".png":
        print "Bad extension: ",filename
        filename = filename + ".png"
    #else: #should be fine
    #transform to image: may be special for depth: should not need scaling
    #if image.shape[2]==1:
    #    #depth: put in range 0-255
    #    image = (image.astype(np.float32)*(255.0/self.max_depth)).astype(np.uint8)
    #else: color should be normal
    #save
    #result = Image.fromarray(image)
    #result.save(filename)
    cv2.imwrite(filename, image)#, cv2.CV_16U)#? #IPLImage

'''
The folowing are all display/debug functions
'''
def display_color(image, brief = False):
    print "Displaying color"
    #cv2.imshow('Color',image)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    cv2.imshow('Color',image.astype(np.uint8))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    #sometimes destroy windows doesn't? Does it work when 0 is hit vs when the gui x is used?

'''
Function: find all image files recursively in directory "data"
    *collect the list of tar files & list of files in each tar*This way we don't have to extract them, just each image as we need it...
'''
def find_tared_data(directory='original/tared'):
    print "Finding Data ",directory
    #check color and real vs generated
    #check directoryList not emtpy
    files = [] #store the path up to the tar (.../.../...tar), and have its value be the list of files in the tar
    for dirs, subDirs, filenames in os.walk(directory):#check walks correct location 
        print "DEBUG ",type(subDirs)
        #we expect these to be tar files now, we want to look inside
        for item in filenames:
            print item,',',dirs
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
                    if not ("_depth" in pic) and not ("_mask" in pic) and ('.png' in pic):
                        #print "File: ",type(pic),", ",pic
                        files.append((key, pic[:-4], len(contents)))
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
        if tarinfo.name == filename+"_Not.txt" or tarinfo.name == filename+".txt" or tarinfo.name == filename+".png" or tarinfo.name == filename+"_depth.png":
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
    find_mean(directories)
    print "Ending in Main..."
    sys.exit()