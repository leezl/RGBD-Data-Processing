'''
Python2.7
Version of rgbPickler which loads from .tar files into pickledGZipped files.

Data is assumed to be of format: image, depth image, mask image, text of positive sentences, and text of negative list.
This is also currently set for Kinect data, notably the scales of the images: 640,480,4.  The images must be the same shape.
This could be changed.

* This version stops pickling if ctrl c is hit, and stores a save point, so that pickling can be continued later.

'''

import sys, os
import tarfile
import gzip, cPickle
import numpy as np
import cv2
import shutil
import random
import signal
import threading
import time

'''
This class is responsible for finding the data in the provided folders, 
loading the data, findign the meta data, and creating pickled batches of the data.

This is intended for use with Cuda-Convnet, though it could be adapted for other purposes.
'''

class TaredPickler:

    def __init__(self, dataDirs = ['original/tared', 'original/lab']):
        #flag for whether we have processed everything. For use with a thread that checks for Ctrl+C
        self.done=False
        #Just printng the current directory for reference
        print os.getcwd()
        #if the progressLog (our save point) does not exist, start over
        if not os.path.isfile(os.getcwd()+'/progressLog'):
            #start fresh batch
            print "No Previous Log Saved"
            self.set_up(dataDirs)
        else:
            #have a save point
            #return here later
            self.originalDir = os.getcwd()
            print "Loading Previous Log"
            #load progress from file
            fo = open('progressLog', 'rb')
            diction = cPickle.load(fo)
            fo.close()
            #remove log:
            os.remove('progressLog')
            #
            self.directoryc = diction['directoryc']
            #load fileList
            self.fileList = diction['fileList']
            #load totalDictionary
            self.total_dictionary = diction['total_dictionary']
            #load list_dictionary
            self.list_dictionary = diction['list_dictionary']
            #load maxMinPoints
            self.maxMinPoints = diction['maxMinPoints']
            #load meanSum
            self.meanSum = diction['meanSum']
            #load index where we stopped
            self.i = diction['i']
            #load batchSize
            self.batchSize = diction['batchSize']
            self.crop_list = diction['crop_list']
            self.labels = diction['labels']
            self.data = diction['data']
        #not asked to exit yet
        self.do_not_exit = True
        self.outputLoc = "pickledGZip"
        
    '''
    Sets all variable, finds data list
    '''
    def set_up(self, dataDirs):
        #find all files
        self.originalDir = os.getcwd()
        self.directoryc = []
        self.fileList = []
        # This attemtps to get the complete path to folders in this directory
        for item in dataDirs:
            os.chdir(item)
            self.directoryc += [os.getcwd()]
            self.fileList += self.find_tared_data(directory=self.directoryc[-1])
            os.chdir(self.originalDir)
        #shuffle
        random.shuffle(self.fileList)
        #find a fair batch_size here
        numFiles = len(self.fileList)
        print "How many files in all tars? ", numFiles
        #set the batch size 
        find_batch_size(numFiles)
        #self.emergency_quit()
        #store this set's data; so you can see what it tries to do next
        f = open('processedDataTared.txt', 'w')
        f.write('Number of Files '+str(numFiles)+'\n')
        f.write('Batch Size '+str(self.batchSize)+'\n')
        f.write('Number of Batches '+str(numFiles/self.batchSize)+'\n')
        #store list of files used?
        #for path, picFile in fileList:
        #   f.write(picFile)
        f.close()
        #totalDictionary: for this data it is currently only the filename: apple, banana, foodbox...?
        self.total_dictionary = self.load_dictionary(self.fileList)
        #a list verison for index fetching
        self.list_dictionary = self.total_dictionary.keys()
        #maxMinPoints: tracks the largest crop box for the data: first two are high, stupid, but the other code is like that...change now?
        self.maxMinPoints = [900,900,-1,-1]
        #mean image:
        #THIS SHOULD BE SET AUTOMATICALLY: load an image, set the shape...
        self.meanSum = np.zeros((480,640,4)).astype(np.single)
        self.i = 0
        #crop_list: collect the crop box coords for each image
        self.crop_list = []
        #labels: store the main label for each image as we load them
        self.labels = []
        #data: store the stacked color and depth as np.single
        self.data = []

    '''
    Attempts to find a batch size which leads to an equal division of images
    '''
    def find_batch_size(self, numFiles, goalSize=50, minSize=30, maxSize=100):
        #find batch size that results in equal size batches, of less than 50 per batch
        #initial batchSize (smallest)
        self.batchSize = minSize
        #find next even division
        while (numFiles%self.batchSize != 0) and self.batchSize<maxSize:#(batchSize != numFiles):
            self.batchSize = self.batchSize + 1
        if self.batchSize>=maxSize:
            drop = numFiles%goalSize
            for i in range(0, drop):
                self.fileList.pop() #should be insignificant...even within an item...
            self.batchSize = goalSize
        print "Batch Size ",self.batchSize
        print "Number of Batches ",numFiles/self.batchSize


    '''
    This begins the pickler and then watches for the shutdown signal.
    '''
    def run(self):
        #create thread
        self.t = threading.Thread(target=self.main_pickler, args=())
        #register CTRL C handler
        signal.signal(signal.SIGINT, self.signal_handler_thread)
        #start the main pickler thread
        self.t.daemon = True
        self.t.start()
        #now, correct way to wait is...
        #self.t.join()
        while not self.done:
            time.sleep(0.1)

    '''
    Function: find all image files recursively in directory "data"
        *collect the list of tar files & list of files in each tar*This way we don't have to extract them, just each image as we need it...
    '''
    def find_tared_data(self, skip=5, directory='original/tared'):
        print "Finding Data"
        #check color and real vs generated
        #check directoryList not emtpy
        files = [] #store the path up to the tar (.../.../...tar), and have its value be the list of files in the tar
        for dirs, subDirs, filenames in os.walk(directory):#check walks correct location
            #we expect these to be tar files now, we want to look inside
            for item in filenames:
                print item
                #if it really is a tar file:
                if tarfile.is_tarfile(item):#do we need path too?
                    tared = tarfile.open(item, 'r')
                    contents = tared.getnames()
                    key = os.path.join(dirs, item)
                    #print "Key: ",key
                    #print "Filtered Contents: "
                    if len(contents)>200:
                        for j, pic in enumerate(contents):
                            #print "Contents: ",type(pic),", ",pic
                            #check if pic is the original color picture (not crop, not mask etc)
                            if (j%skip == 0) and (not "_depth" in pic) and (not "_loc" in pic) and (not "_mask" in pic) and (not "_crop" in pic) and '.png' in pic:
                                #print "File: ",type(pic),", ",pic
                                files.append((key, pic, len(contents)))
                    else:
                        for pic in contents:
                            #print "Contents: ",type(pic),", ",pic
                            #check if pic is the original color picture (not crop, not mask etc)
                            if (not "_depth" in pic) and (not "_loc" in pic) and (not "_mask" in pic) and (not "_crop" in pic) and '.png' in pic:
                                #print "File: ",type(pic),", ",pic
                                files.append((key, pic, len(contents)))
                    #clear for next file...shouldn't be needed now that I look
                    #members[:] = []
                    tared.close()
        #return to previous Directory
        return files

    '''
    A debug function to check what you are loading
    '''
    def display_color(self, image, brief = False):
        print "Displaying color"
        #cv2.imshow('Color',image)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        cv2.imshow('Color',image.astype(np.uint8))
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        #sometimes destroy windows doesn't? Does it work when 0 is hit vs when the gui x is used?

    '''
    Function: use mask to find max and min values around object
    '''
    def get_crop_box(self, image, margin =10):
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
    Function: parse filename: pulls out the object name (apple) from the filename, if it is there...
    If your data changes at all, this won't work.
    '''
    def parse_name(self, filename):
        #strip path
        #print "What ",filename
        sub = filename.split('/')
        #print sub
        #print sub[-2]
        #sub = sub[-2].split('_')
        #print sub[0]
        #print sub[-2][:-2] 
        #self.emergency_quit()
        return sub[-2][:-2] 

    '''
    Function: Load total_dictionary (based on filenames)
    '''
    def load_dictionary(self, fileList):
        #load from fileList
        total_dictionary = {}
        #for each picture in tar file
        for filepath, filename, length in fileList:
            #grab the object name
            name = self.parse_name(filename)
            #add to dictionary/increment
            if name in total_dictionary:
                total_dictionary[name] = total_dictionary[name] + 1
            else:
                total_dictionary[name] = 1
        #Need a none of the above label for no match? 
        total_dictionary['NONE'] = 1
        return total_dictionary

    '''
    Function: DEBUG: escape early if we see something bad
    '''
    def emergency_quit(self):
        s = raw_input('--> ')
        if s=='q':
            sys.exit()

    '''
    Function: tries to load only needed file at once...
    '''
    def current_file(self, members, filename):
        for tarinfo in members:
            if tarinfo.name == filename or tarinfo.name == filename[:len(filename)-4]+"_depth.png" or tarinfo.name == filename[:len(filename)-4]+"_mask.png" \
                or tarinfo.name == filename[:len(filename)-9]+"depth.png" or tarinfo.name == filename[:len(filename)-4]+"_crop.txt":
                yield tarinfo

    '''
    
    '''
    def reflect_image(self, name, coords, image, depth):
        #reflect image
        imageRef = image[:,::-1,:]
        #reflect mask/coords
        #maskRef = mask[::-1,:,:]
        coordsRef = ( image.shape[1]-coords[2], coords[1], image.shape[1]-coords[0], coords[3])
        #reflect depth
        depthRef = depth[:,::-1]
        #return...or just add...?
        totalImageRef = np.dstack((imageRef, depthRef))
        self.labels.append(name)
        self.data.append(totalImageRef)
        self.crop_list.append(coordsRef)
        # find mean sum
        assert totalImageRef.shape == self.meanSum.shape, \
            "image is different shape than mean "+str(totalImageRef.shape)+','+str(self.meanSum.shape)
        self.meanSum = np.add(self.meanSum, totalImageRef)

    '''
    Function: main 
     * Finds files
     * loads each
         * adds to sum
         * finds crop
         * takes name of file and adds as label
         * 
    '''

    def main_pickler(self):
        print "Pickling..."
        self.pickling = True
        #iterate through tars
        print "Current Progress ",self.i," of ",len(self.fileList)
        otherI = self.i
        for index in range(otherI, len(self.fileList)):
            #print "donotexit ", self.do_not_exit
            if self.do_not_exit:
                #print "iterating through files"
                (path, picFile, length) = self.fileList[index]
                #open tar for this loop
                #print "opening tarfile "+str(path)
                assert tarfile.is_tarfile(path), str(path)+" is not a tarfile"
                tared = tarfile.open(path, 'r')
                #may be necessary to extractall here, then delete each picture as we transform it to pickled data...
                #NOTE extract method has some exceptions which it does not catch; extractAll catches more
                #t.extractall()
                print "path and file and length: ",self.i,',',path,',',picFile,',',length
                tared.extractall(members=self.current_file(tared, picFile))
                tared.close()
                #emergency_quit()
                # get label value: need name, and fidn index of name
                name = self.parse_name(picFile)
                # load image: tar is open, just get member
                image = cv2.imread(picFile, cv2.IMREAD_UNCHANGED)
                assert image != None, "No Image Loaded"
                # check member loaded correctly: is image?
                #display_color(image)
                # load depth
                depth = cv2.imread(picFile[:len(picFile)-4]+"_depth.png", cv2.IMREAD_UNCHANGED)
                #print "PATH TEST ",os.path.exists(picFile[:len(picFile)-4]+"_depth.png")
                #display_color(depth)
                # load mask
                mask = cv2.imread(picFile[:len(picFile)-4]+"_mask.png", cv2.IMREAD_UNCHANGED)
                if depth != None and mask != None:
                    store=True
                    #print type(depth),',',type(mask)
                    #display_color(mask)
                    # find cropping
                    coords = self.get_crop_box(mask)
                    #display_color(image[coords[0]:coords[2], coords[1]:coords[3],:])
                elif os.path.exists(picFile[:len(picFile)-4]+"_crop.txt") and os.path.exists(picFile[:len(picFile)-9]+"depth.png"):
                    store=True
                    #if we have the other depth and mask:
                    #load crop
                    #print "Crop file ",picFile[:len(picFile)-4]+"_crop.txt"
                    f=open(picFile[:len(picFile)-4]+"_crop.txt",'r')
                    coords = tuple([int(item) for item in f.read().split(',')])
                    coords = (coords[1],coords[0],coords[3],coords[2])
                    f.close()
                    #print coords
                    #self.emergency_quit()
                    #load depth 
                    depth = cv2.imread(picFile[:len(picFile)-9]+"depth.png", cv2.IMREAD_UNCHANGED)
                else:
                    #missing depth or mask, so can't use
                    #tared.close()
                    store=False
                if store:
                    # add label value to labels for this batch, now that we know it will be in the batch
                    self.labels.append(self.list_dictionary.index(name))
                    # store cropping of image for this batch
                    self.crop_list.append(coords)
                    # check overall cropping update
                    if self.maxMinPoints[2]<coords[2]: # max x
                        self.maxMinPoints[2] = coords[2]
                    if self.maxMinPoints[3]<coords[3]: # max y
                        self.maxMinPoints[3] = coords[3]
                    if self.maxMinPoints[0]>coords[0]: # min x
                        self.maxMinPoints[0] = coords[0]
                    if self.maxMinPoints[1]>coords[1]: # min y
                        self.maxMinPoints[1] = coords[1]
                    #self.display_color(image[coords[0]:coords[2],coords[1]:coords[3],:])
                    #3self.emergency_quit()
                    #make single precision
                    image.astype(np.single)
                    depth.astype(np.single)
                    # Stack the data 
                    totalImage = np.dstack((image, depth))
                    # add to current batch data
                    self.data.append(totalImage)
                    # find mean sum
                    assert totalImage.shape == self.meanSum.shape, \
                        "image is different shape than mean "+str(totalImage.shape)+','+str(self.meanSum.shape)
                    self.meanSum = np.add(self.meanSum, totalImage)
                    #print self.meanSum.dtype
                    #reflect picture for more samples...
                    if length<200:
                        self.reflect_image(name, coords, image, depth)
                #clear the extracted directory (so we don't take up that much space) Assume: all in same folder (rgbd...)
                dirToDel = picFile.split('/')[0]
                #print dirToDel
                #self.emergency_quit()
                shutil.rmtree(dirToDel)#be careful here
                # check if batch is full; if batch is full, store it and clear stuff
                #print "i value ",i
                if (self.i+1)%self.batchSize == 0:
                    print "on image ",self.i," storing"
                    #set outputfile
                    filenum = (self.i)/self.batchSize
                    print "Pickling Batch: ",self.outputLoc+"/data_batch_"+str((self.i)/self.batchSize)
                    if filenum-1>0:
                        assert os.path.exists(self.outputLoc+"/data_batch_"+str(filenum-1)), \
                            "Previous batch does not exist, "+str(filenum)+','+str(self.batchSize)+','+str(self.i)
                    outputFileName = self.outputLoc+"/data_batch_"+str((self.i)/self.batchSize)
                    if not os.path.exists(self.outputLoc):
                        os.makedirs(self.outputLoc)
                    outputFile = gzip.open(outputFileName, 'wb')
                    assert len(self.data) == len(self.labels), "Not the same number of data and labels "+str(len(self.data))+','+str(len(self.labels))
                    #pickle
                    cPickle.dump({'data' : np.array(self.data), 'labels' : np.array(self.labels), 
                        'crop_boxes' : self.crop_list}, outputFile, protocol=cPickle.HIGHEST_PROTOCOL)
                    outputFile.close()
                    #clear
                    self.data[:] = []
                    self.labels[:] = []
                    self.crop_list[:] = []
                #print self.i,',',len(self.data) 
                self.i = self.i + 1
            else:
                #flagged to exit: store everything
                print "ended?"
                #return only after finishing a batch
                return
        # finish mean calculation after all images
        #divide mean
        #rint "FileList ",len(self.fileList)
        dividor = len(self.fileList) * np.ones((480,640,4), dtype=float)
        #rint self.meanSum[0,0],',',dividor[0,0]
        #data_mean...
        data_mean = np.divide(self.meanSum, dividor)
        #elf.display_color(data_mean)
        #rint data_mean.dtype,',',data_mean[0,0]
        # finish overall label_names
        label_names = self.total_dictionary.keys()
        # finish num_vis (image shape)
        num_vis = (480,640,4)
        # pickle above as meta data
        meta = {'label_names':label_names, 'num_vis' : num_vis, 'total_dictionary' : self.total_dictionary, 
            'data_mean' : data_mean, 'overall_crop' : self.maxMinPoints}
        #pickle the total thing
        outputFileName = self.outputLoc+"/batches.meta"
        if not os.path.exists(self.outputLoc):
            os.makedirs(self.outputLoc)
        outputFile = gzip.open(outputFileName, 'wb')
        cPickle.dump(meta, outputFile, protocol=cPickle.HIGHEST_PROTOCOL)
        self.done = True

    '''
    Signals can only be caught by main, so while this is labeled thread, it is used by main to reclaim the thread and close properly
    '''
    def signal_handler_thread(self, signal, frame):
        self.do_not_exit = False
        self.t.join()
        #if we're pickling already wait and save
        if self.pickling:
            print "Waiting for current file to complete..."
            #join thread: force current batch to finish
            self.t.join()
            print "Saving Progress"
            diction = {}
            #load fileList
            diction['fileList'] = self.fileList
            #load totalDictionary
            diction['total_dictionary'] = self.total_dictionary
            #load list_dictionary
            diction['list_dictionary'] = self.list_dictionary
            #load maxMinPoints
            diction['maxMinPoints'] = self.maxMinPoints
            #load meanSum
            diction['meanSum'] = self.meanSum
            #load index where we stopped
            diction['i'] = self.i
            #load batchSize
            diction['batchSize'] = self.batchSize
            diction['crop_list'] = self.crop_list 
            diction['labels'] = self.labels
            diction['data'] = self.data
            diciton['directoryc'] = self.directoryc
            print "Progress at save time ",self.i," of ",len(self.fileList)
            #save progress to file
            fo = open('progressLog', 'wb')
            cPickle.dump(diction, fo)
            fo.close()
        # else just exit
        print 'Exiting Program due to signal'
        self.done = True
        sys.exit(0)

    def signal_handler_main(self, signal, frame):
        #if we're pickling already wait and save
        self.do_not_exit = False
        while not self.done:
            time.sleep(0.1)
        # else just exit
        print 'Exiting Program due to signal'
        sys.exit(0)

if __name__ == "__main__":
    pickler = TaredPickler()
    pickler.run() # need this to work correctly
    print "Ending in Main..."
    sys.exit()
