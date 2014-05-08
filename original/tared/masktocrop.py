'''
Finds all tars
unpacks each
finds each image that has a mask
loads the mask
finds the crop values
saves the crop values
re-tars the data
'''

import sys, os
import tarfile
import numpy as np
import cv2
import shutil

def find_crops():
    #find tar files
    #find files in tar files
    fileList = find_tared_data('.')
    print "files to process ",len(fileList)
    #for each file
    for index in range(0, len(fileList)):
        #print "iterating through files"
        (path, picFile, length) = fileList[index]
        #for each mask file:
        assert tarfile.is_tarfile(path), str(path)+" is not a tarfile"
        tared = tarfile.open(path, 'r')
        try:
            #t.extractall()
            print "path and file and length: ",path,',',picFile,',',length
            try:
                tared.extractall(members=current_file(tared, picFile))
                tared.close()
                #load image: tar is open, just get member
                image = cv2.imread(picFile, cv2.IMREAD_UNCHANGED)
                assert image != None, "No Image Loaded"
                #find the crop values
                #display_color(image)
                crop = get_crop_box(image)
                #debug: view cropped image
                #display_image_with_crop(image, crop)
                #save crop values
                print '\n',picFile,',   ', picFile[:-8]+"crop.txt"+'\n'
                #f = open(os.path.join(directory,picFile[:-8]+"crop.txt"),'w')
                f = open(picFile[:-8]+"crop.txt", 'w')
                f.write(str(crop[0])+' '+str(crop[1])+' '+str(crop[2])+' '+str(crop[3]))
                f.close()
                #add crop file to tar file
                tared = tarfile.open(path, 'a')
                #TarFile.add(name, arcname=None, recursive=True, exclude=None, filter=None)
                tared.add(picFile[:-8]+"crop.txt")
            finally:
                #remove extracted directory
                dirToDel = picFile.split('/')[0]
                #print dirToDel
                #emergency_quit()
                shutil.rmtree(dirToDel)#be careful here
        finally:
            #close the tar
            tared.close()


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

#display image
def display_image_with_crop(image, crop, brief=False):
    #use matplot lib here, just because it lets us see grid position of mouse
    img = np.copy(image)
    for i in range(crop[0]+1, crop[2]-1):
        img[crop[1]+1, i] = (200)
        img[crop[3]-1, i] = (200)
    for i in range(crop[1]+1, crop[3]-1):
        img[i, crop[0]+1] = (200)
        img[i, crop[2]-1] = (200)
    display_color(img)
    #THIS IS THE GREYSCALE VERSION

'''
Function: use mask to find max and min values around object
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
    result = ( max(colLow-margin, 0), max(rowLow-margin, 0), min(colHigh+margin, image.shape[1]), min(rowHigh+margin, image.shape[0]) )
    #display_color(image[result[0]:result[2],result[1]:result[3]])
    #emergency_quit()
    #print (min(rowHigh+margin, image.shape[0]), min(colHigh+margin, image.shape[1]), max(rowLow-margin, 0), max(colLow-margin, 0))
    return result

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
        #we expect these to be tar files now, we want to look inside
        for item in filenames:
            print item
            #if it really is a tar file:
            if tarfile.is_tarfile(item):#do we need path too? yes
                tared = tarfile.open(item, 'r')
                contents = tared.getnames()
                key = os.path.join(dirs, item)
                #print "Key: ",key
                #print "Filtered Contents: "
                for pic in contents:
                    #print "Contents: ",type(pic),", ",pic
                    #check if pic is the original color picture (not crop, not mask etc)
                    if ("_mask" in pic) and '.png' in pic:
                        #print "File: ",type(pic),", ",pic
                        files.append((key, pic, len(contents)))
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
        if tarinfo.name == filename:
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
    find_crops()
    print "Ending in Main..."
    sys.exit()