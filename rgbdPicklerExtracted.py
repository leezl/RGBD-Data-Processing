'''
This program finds nearby files that are not already processed, OR reprocesses all files.

These files are: RGBD data: Color, Depth and Mask

These images are  split into batches of size X (no idea what a good size is yet...figure it out by...?). These are used to find a mean for the data, which is stored with the meta data. 

The images are pickled as np.single precision arrays...
Other options:
    * store color and dpeth separate as uint8 and uint16
    * store color and depth flat, and reshape later

Questions:
* Does it matter if we later take smaller patches, if we have already subtracted the mean? Maybe: If we need to add it back for display...
* If some of our images are larger than our "small" patch, again, how will mean be affected?
'''

#from collecitons import defaultdict
#import...
import sys, os
import numpy as np
import cv2
import random

'''
The folowing are all display/debug functions
'''
def display_color(image, brief = False):
    print "Displaying color"
    #plt.imshow(image.astype(np.uint8))
    #if brief:
    #    plt.pause(.1)
    #    plt.draw()
    #else:
    #    plt.show()
    #plt.close()
    cv2.imshow('Color',image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

'''
Function: find all image files recursively in directory "original"
'''
def find_data(dataDir = 'original/extracted', skip=5):
    print "Finding Data"
    #create list with glob
    fileList = []
    #check color and real vs generated
    originalDir = os.getcwd()
    #os.chdir('original/apple_1')
    os.chdir(dataDir)#TODO: SWITCH BACK TO ALL FOLDERS
    #check directoryList not emtpy
    directoryc = os.getcwd()
    files = []
    for dirs, subDirs, filenames in os.walk(directoryc):#check walks correct location
        for i, item in enumerate(filenames):
            x = os.path.join(dirs, item)
            y = x.split('/')#take off first 8
            #only collect rgb image names
            if (i%skip == 0) and (not "_depth" in y[-1]) and (not "_loc" in y[-1]) and (not "_mask" in y[-1]) and (not "_crop" in y[-1]):
                #print y
                index = y.index('original')
                y = y[index+1:]
                title =''
                for stuff in y:
                    title = title + stuff + '/'
                title = title[:len(title)-1]
                #print title
                #raw_input('Enter')
                files.append('/'+title)#-'/home/lieslw/Projects/shapeTest/ShapeData/realData/')
    #return to previous Directory
    os.chdir(originalDir)
    return (files, directoryc)

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
    #strip ending
    result =""
    #DEBUG
    #print "Full Filename: ",filename
    sub = filename.split('/')
    #print "Sub ",sub
    subsub = sub[1].split('_')
    #print "SubSub ",subsub
    for item in subsub[:len(subsub)-1]:
        result = result+'_'+item
    #DEBUG
    #print "Returned label: ",result[1:]
    return result[1:] #cut off extra _ at start, opps

'''
Function: Load total_dictionary
'''
def load_dictionary(fileList):
    #load from fileList
    total_dictionary = {}
    for filename in fileList:
        name = parse_name(filename)
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
    fileList, directoryc = find_data()
    #find a fair batch_size here
    numFiles = len(fileList)
    #print "How Many files? ", numFiles
    #find batch size that results in equal size batches, of less than 50 per batch
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
    #store this batches data
    f = open('processedDataExtracted.txt', 'w')
    f.write('Number of Files '+str(numFiles)+'\n')
    f.write('Batch Size '+str(batchSize)+'\n')
    f.write('Number of Batches '+str(numFiles/batchSize)+'\n')
    #store list of files used?
    #for path, picFile in fileList:
    #   f.write(picFile)
    f.close()
    #totalDictionary: for this data it is currently only the filename: apple, banana, foodbox...?
    total_dictionary = load_dictionary(fileList)
    #a lsit verison for index fetching
    list_dictionary = total_dictionary.keys()
    #maxMinPoints: tracks the largest crop box for the data
    maxMinPoints = [0,0,900,900]
    #mean image:
    meanSum = np.zeros((480,640,4))
    #crop_list: collect the crop box coords for each image
    crop_list = []
    #labels: store the main label for each image as we load them
    labels = []
    #data: store the stacked color and depth as np.single
    data = []
    #shuffle training data so we don't adapt to one object first
    random.shuffle(fileList)
    #iterate through images
    for i,filename in enumerate(fileList):
        #directoryc+imageName
        name = parse_name(filename)
        labels.append(list_dictionary.index(name))
        #load color image
        x = cv2.imread(directoryc+filename[:len(filename)-4]+".png", cv2.IMREAD_UNCHANGED)
        x.astype(np.single)
        #load depth and concatenate to image...
        y = cv2.imread(directoryc+filename[:len(filename)-4]+"_depth.png", cv2.IMREAD_UNCHANGED)
        #load mask
        z = cv2.imread(directoryc+filename[:len(filename)-4]+"_mask.png", cv2.IMREAD_UNCHANGED)
        #Find crop from mask
        coords = get_crop_box(z)
        crop_list.append(coords)
        #Check max and min
        # check overall cropping update
        if maxMinPoints[2]<coords[2]: # max x
            maxMinPoints[2] = coords[2]
        if maxMinPoints[3]<coords[3]: # max y
            maxMinPoints[3] = coords[3]
        if maxMinPoints[0]>coords[0]: # min x
            maxMinPoints[0] = coords[0]
        if maxMinPoints[1]>coords[1]: # min y
            maxMinPoints[1] = coords[1]
        #stack the color and depth
        image = np.dstack((x,y))
        data.append(image)

        #add to mean
        assert image.shape == meanSum.shape, "image is different shape than mean "+str(image.shape)+','+str(meanSum.shape)
        meanSum = np.add(meanSum, image)

        #check length of labels, or image list etc: if == batch size then pickle and clear
        if (i+1)%batchSize == 0:
            #set outputfile
            outputFileName = outputLoc+"/data_batch_"+str(i/batchSize)
            if not os.path.exists(outputLoc):
                os.makedirs(outputLoc)
            outputFile = open(outputFileName, 'wb')
            #store data, labels, and cropboxes
            cPickle.dump({'data' : np.array(dataAll), 'labels' : np.array(labelsAll), 
            'crop_boxes' : crop_list}, outputFile)
            #clear data, labels, and crop_boxes
            data[:] = []
            labels[:] = []
            crop_list[:] = []
    #divide mean
    dividor = len(fileList) * np.ones((480,640,4), dtype=float)
    #data_mean...
    data_mean = np.divide(meanSum,dividor)
    #label_names
    label_name = total_dictionary.keys()
    #num_vis
    num_vis = (480,640,4)

    #pickle as batch meta
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
