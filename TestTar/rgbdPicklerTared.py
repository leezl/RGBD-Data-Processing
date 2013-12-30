'''
Version of rgbPickler which loads from .tar files into pickled files.

* Need to shuffle data...how to do this? Swap dictionary format to be 
list of tuples: add each (key, value pair) but allow the keys to repeat. 
This will be much slower (more openning and closing of tars...). Still
saves space.
'''

import sys, os
import tarfile
import cPickle
import numpy as np
import cv2
import shutil
import random

'''
Function: find all image files recursively in directory "data"
    *collect the list of tar files & list of files in each tar*This way we don't have to extract them, just each image as we need it...
'''
def find_tared_data(dataDir = 'original/tared', skip=5):
    print "Finding Data"
    #check color and real vs generated
    originalDir = os.getcwd()
    os.chdir(dataDir)
    #check directoryList not emtpy
    directoryc = os.getcwd()
    files = [] #store the path up to the tar (.../.../...tar), and have its value be the list of files in the tar
    for dirs, subDirs, filenames in os.walk(directoryc):#check walks correct location
        #we expect these to be tar files now, we want to look inside
        for item in filenames:
            #if it really is a tar file:
            if tarfile.is_tarfile(item):#do we need path too?
                t = tarfile.open(item, 'r')
                contents = t.getnames()
                key = os.path.join(dirs, item)
                #print "Key: ",key
                #print "Filtered Contents: "
                if len(contents)>200:
                    for i, pic in enumerate(contents):
                        #print "Contents: ",type(pic),", ",pic
                        #check if pic is the original color picture (not crop, not mask etc)
                        if (i%skip == 0) and (not "_depth" in pic) and (not "_loc" in pic) and (not "_mask" in pic) and (not "_crop" in pic):
                            #print "File: ",type(pic),", ",pic
                            files.append((key, pic))
                else:
                    for pic in contents:
                        #print "Contents: ",type(pic),", ",pic
                        #check if pic is the original color picture (not crop, not mask etc)
                        if (not "_depth" in pic) and (not "_loc" in pic) and (not "_mask" in pic) and (not "_crop" in pic):
                            #print "File: ",type(pic),", ",pic
                            files.append((key, pic))
                #clear for next file...shouldn't be needed now that I look
                #members[:] = []
                t.close()
    #return to previous Directory
    os.chdir(originalDir)
    return (files, directoryc)

'''
The folowing are all display/debug functions
'''
def display_color(image, brief = False):
    print "Displaying color"
    cv2.imshow('Color',image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    #sometimes destroy windows doesn't? Does it work when 0 is hit vs when the gui x is used?

'''
Function: use mask to find max and min values around object
#TODO: fix for inverse colors? masks are reversed?
'''
def get_crop_box(image, margin =10):
    #display_color(image)
    if len(image.shape) >2:
        checkValRow = image.shape[0] * image.shape[2] * 255
        checkValCol = image.shape[1] * image.shape[2] * 255
    else:
        checkValRow = image.shape[0] * 255
        checkValCol = image.shape[1] * 255
    #print checkValRow,',',checkValCol
    rowLow=colLow=-1
    rowHigh=colHigh=-1
    chunk=False
    #rows
    for i in range(0,image.shape[0]):
        rowS = np.sum(image[i,:].flatten())
        #print "Row Sums {}".format(rowS)
        if chunk==True:
            #skip if we have found and want only first chunk...
            pass
        elif rowLow==-1 and rowS >0:#< checkValRow:
            #current row contains non-black, which we haven't seen
            rowLow = i
        elif rowS >0:#< checkValRow:
            #current row contains non-black which we have seen
            rowHigh = i
        elif rowHigh!=-1 and rowS<= 0:#checkValRow:
            #current row is all black
            if rowHigh-rowLow>10:
                #this allows cutoff of a chunk in the scene...
                #chunk=True
                pass
            else:
                #chunk found was too small
                rowLow=rowHigh=-1
    chunk=False
    #cols
    for j in range(0, image.shape[1]):
        colS = np.sum(image[:,j].flatten())
        #print "COL Sums {}".format(colS)
        if chunk==True:
            pass
        elif colLow==-1 and colS >0:#< checkValCol:
            colLow = j
        elif colS >0:#< checkValCol:
            colHigh = j
        elif colHigh!=-1 and colS<=0:#>=checkValCol:
            if colHigh-colLow>10:
                #chunk=True
                pass
            else:
                colLow=colHigh=-1
    result = ( max(rowLow-margin, 0), max(colLow-margin, 0), min(rowHigh+margin, image.shape[0]), min(colHigh+margin, image.shape[1]) )
    #display_color(image[result[0]:result[2],result[1]:result[3]])
    #emergency_quit()
    #print (min(rowHigh+margin, image.shape[0]), min(colHigh+margin, image.shape[1]), max(rowLow-margin, 0), max(colLow-margin, 0))
    return result

'''
Function: parse filename: pulls out the object name (apple) from the file
'''
def parse_name(filename):
    #strip path
    sub = filename.split('/')
    return sub[1] 

'''
Function: Load total_dictionary
'''
def load_dictionary(fileList):
    #load from fileList
    total_dictionary = {}
    #for each picture in tar file
    for filepath,filename in fileList:
        #grab the object name
        name = parse_name(filename)
        #add to dictionary/increment
        if name in total_dictionary:
            total_dictionary[name] = total_dictionary[name] + 1
        else:
            total_dictionary[name] = 1
    return total_dictionary

'''
Function: DEBUG: escape early if we see something bad
'''
def emergency_quit():
    s = raw_input('--> ')
    if s=='q':
        sys.exit()

'''
Function: tries to load only needed file at once...
'''
def current_file(members, filename):
    for tarinfo in members:
        if tarinfo.name == filename or tarinfo.name == filename[:len(filename)-4]+"_depth.png" or tarinfo.name == filename[:len(filename)-4]+"_mask.png":
            yield tarinfo

'''
Function: main 
 * Finds files
 * loads each
     * adds to sum
     * finds crop
     * takes name of file and adds as label
     * 
'''

def main_pickler():
    outputLoc = "pickled"
    #find all files
    fileList, directoryc = find_tared_data()
    #shuffle
    random.shuffle(fileList)
    #find a fair batch_size here
    numFiles = len(fileList)
    print "How many files in all tars? ", numFiles
    #find batch size that results in equal size batches, of less than 50 per batch
    #initial batchSize (smallest)
    batchSize = 30
    #find next even division
    while (numFiles%batchSize != 0) and batchSize<100:#(batchSize != numFiles):
        batchSize = batchSize + 1
    if batchSize>=100:
        drop = numFiles%50
        for i in range(0, drop):
            fileList.pop() #should be insignificant...even within an item...
        batchSize = 50
    print "Batch Size ",batchSize
    print "Number of Batches ",numFiles/batchSize
    emergency_quit()
    #store this batches data
    f = open('processedDataTared.txt', 'w')
    f.write('Number of Files '+str(numFiles)+'\n')
    f.write('Batch Size '+str(batchSize)+'\n')
    f.write('Number of Batches '+str(numFiles/batchSize)+'\n')
    #store list of files used?
    #for path, picFile in fileList:
    #   f.write(picFile)
    f.close()
    #totalDictionary: for this data it is currently only the filename: apple, banana, foodbox...?
    total_dictionary = load_dictionary(fileList)
    #a list verison for index fetching
    list_dictionary = total_dictionary.keys()
    #maxMinPoints: tracks the largest crop box for the data: first two are high, stupid, but the other code is like that...change now?
    maxMinPoints = [900,900,-1,-1]
    #mean image:
    meanSum = np.zeros((480,640,4))
    #crop_list: collect the crop box coords for each image
    crop_list = []
    #labels: store the main label for each image as we load them
    labels = []
    #data: store the stacked color and depth as np.single
    data = []
    #iterate through tars
    for i,(path,picFile) in enumerate(fileList):
        #open tar for this loop
        t = tarfile.open(path, 'r')
        #may be necessary to extractall here, then delete each picture as we transform it to pickled data...
        #NOTE extract method has some exceptions which it does not catch; extractAll catches more
        #t.extractall()
        print picFile
        t.extractall(members=current_file(t, picFile))
        #emergency_quit()
        # get label value: need name, and fidn index of name
        name = parse_name(picFile)
        # load image: tar is open, just get member
        image = cv2.imread(picFile, cv2.IMREAD_UNCHANGED)
        # check member loaded correctly: is image?
        #display_color(image)
        # load depth
        depth = cv2.imread(picFile[:len(picFile)-4]+"_depth.png", cv2.IMREAD_UNCHANGED)
        #display_color(depth)
        # load mask
        mask = cv2.imread(picFile[:len(picFile)-4]+"_mask.png", cv2.IMREAD_UNCHANGED)
        if depth != None and mask != None:
            #print type(depth),',',type(mask)
            # add label value to labels for this batch, now that we know it will be in the batch
            labels.append(list_dictionary.index(name))
            #display_color(mask)
            # find cropping
            coords = get_crop_box(mask)
            #display_color(image[coords[0]:coords[2], coords[1]:coords[3],:])
            # store cropping of image for this batch
            crop_list.append(coords)
            # check overall cropping update
            if maxMinPoints[2]<coords[2]: # max x
                maxMinPoints[2] = coords[2]
            if maxMinPoints[3]<coords[3]: # max y
                maxMinPoints[3] = coords[3]
            if maxMinPoints[0]>coords[0]: # min x
                maxMinPoints[0] = coords[0]
            if maxMinPoints[1]>coords[1]: # min y
                maxMinPoints[1] = coords[1]
            #make single precision
            image.astype(np.single)
            depth.astype(np.single)
            # Stack the data 
            totalImage = np.dstack((image, depth))
            # add to current batch data
            data.append(totalImage)
            # find mean sum
            assert totalImage.shape == meanSum.shape, "image is different shape than mean "+str(totalImage.shape)+','+str(meanSum.shape)
            meanSum = np.add(meanSum, totalImage)
            # check if batch is full; if batch is full, store it and clear stuff
            #print "i value ",i
            if (i+1)%batchSize == 0:
                print "on image ",i," storing"
                #set outputfile
                print "Pickling Batch: ",outputLoc+"/data_batch_"+str(i/batchSize)
                outputFileName = outputLoc+"/data_batch_"+str(i/batchSize)
                if not os.path.exists(outputLoc):
                    os.makedirs(outputLoc)
                outputFile = open(outputFileName, 'wb')
                #pickle
                cPickle.dump({'data' : np.array(data), 'labels' : np.array(labels), 
                    'crop_boxes' : crop_list}, outputFile)
                #clear
                data[:] = []
                labels[:] = []
                crop_list[:] = []
            #close tarfile
            t.close()
            #clear the extracted directory (so we don't take up that much space) Assume: all in same folder (rgbd...)
            dirToDel = picFile.split('/')[0]
            #print dirToDel
            #emergency_quit()
            shutil.rmtree(dirToDel)#be careful here
        else:
            #missing depth or mask, so can't use
            t.close()
    # finish mean calculation after all images
    #divide mean
    dividor = len(fileList) * np.ones((480,640,4), dtype=float)
    #data_mean...
    data_mean = np.divide(meanSum,dividor)
    # finish overall label_names
    label_names = total_dictionary.keys()
    # finish num_vis (image shape)
    num_vis = (480,640,4)
    # pickle above as meta data
    meta = {'label_names':label_names, 'num_vis' : num_vis, 'total_dictionary' : total_dictionary, 
        'data_mean' : data_mean, 'overall_crop' : maxMinPoints}
    #pickle the total thing
    outputFileName = outputLoc+"/batches.meta"
    if not os.path.exists(outputLoc):
        os.makedirs(outputLoc)
    outputFile = open(outputFileName, 'wb')
    cPickle.dump(meta, outputFile)

if __name__ == "__main__":
    main_pickler()
    sys.exit()
