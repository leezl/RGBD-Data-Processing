import sys, os
import numpy as np
import cv2

'''
Function: DEBUG: escape early if we see something bad
'''
def emergency_quit():
    s = raw_input('--> ')
    if s=='q':
        sys.exit()

'''
The folowing are all display/debug functions
'''
def display_color(image, brief = False):
    print "Displaying color"
    cv2.imshow('Color',image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

'''
Find mean of list of images
'''
def find_mean(images):
    summer = np.zeros(images[0].shape)
    for image in images:
        summer = summer + image

    mean = summer/len(images)
    return mean

'''
Find patches of multiple resolutions
'''
def find_multi_res_patches(image, resolutions=[32, 64], stride=-1, finalRes=64):
    cropped_batch = []
    for resolution in resolutions:
        cropped_batch = cropped_batch + find_patches(image, resolution, stride, finalRes)
    return cropped_batch

'''
Find patches of single resolution:
Deprecated: Do not use: fills patches that fall off edge with zeros, which throws off training. 
'''
def find_patches_fill(image, resolution=64, stride=-1, finalRes=64):
    #check stride, reset if invalid
    if stride == -1:
        stride = int(resolution/2)
    #storage for result patches
    patches = []
    #keeping square patches only
    width=height=resolution
    index = 0
    #iterate thrugh rows
    for i in range(0,image.shape[0]-(image.shape[0]%width),stride):#from 0 to right #-width instead?
        #iterate through columns
        for j in range(0,image.shape[1]-(image.shape[1]%height),stride):#from 0 to bottom #-height instead?
            #check if we went over the x & y image boundary; Fill with 0 if we did
            if (i+width>image.shape[0] and j+height>image.shape[1]): 
                #add zeros
                patch = np.zeros((width, height, image.shape[2]))
                patch[0:image.shape[0]-i,0:image.shape[1]-j] = \
                    image[i:image.shape[0], j:image.shape[1]]
            #check if we went over the x image boundary
            elif (i+width>image.shape[0]):
                #add zeros
                patch = np.zeros((width, height, image.shape[2]))
                patch[0:image.shape[0]-i,0:height] = \
                    image[i:image.shape[0], j:j+height]
            #check if we went over the y image boundary
            elif (j+height>image.shape[1]):
                #add zeros
                patch = np.zeros((width, height, image.shape[2]))
                patch[0:width,0:image.shape[1]-j] = \
                    image[i:i+width, j:image.shape[1]]
            #fine: within image, just get patches
            else:
                patch = image[i:i+width, j:j+height]
            #
            remover = np.copy(image)
            remover[i:i+width, j:j+width]=254
            #check that 
            if resolution != finalRes:
                #resize our patch to be correct scale
                #patch = misc.imresize(patch, (finalRes, finalRes), interp='bilinear', mode=None)
                patch = cv2.resize(patch, (finalRes, finalRes))
            patches.append(patch)
            index = index + 1
    return patches#, patchDim

'''
Find patches of single resolution:
If patch falls part way off the edge of the image, slide it back onto the image: don't fill with zeros
'''
def find_patches(image, resolution=64, stride=-1, finalRes=64):
    #check stride, reset if invalid
    if stride == -1:
        stride = int(resolution/2)
    #storage for result patches
    patches = []
    #keeping square patches only
    width=height=resolution
    index = 0
    #iterate through rows
    for i in range(0,  image.shape[0]-(image.shape[0]%width)+1, stride):#from 0 to right #-width instead?
        #iterate through columns
        for j in range(0, image.shape[1]-(image.shape[1]%height)+1, stride):#from 0 to bottom #-height instead?
            #check if we went over the x & y image boundary; Fill with 0 if we did
            if (i+width>image.shape[0] and j+height>image.shape[1]):
                #slide back over
                patch = np.zeros((width, height, image.shape[2]))
                #patch[0:image.shape[0]-i,0:image.shape[1]-j] = image[i:image.shape[0], j:image.shape[1]]
                patch = image[image.shape[0]-width:image.shape[0], image.shape[1]-height:image.shape[1]]
                #DEBUG
                #remover = np.copy(image)
                #remover[image.shape[0]-width:image.shape[0], image.shape[1]-height:image.shape[1]]=254
                #display_color(remover[:,:,:3].astype(np.uint8))
                #display_color(patch[:,:,:3].astype(np.uint8))
            #check if we went over the x image boundary
            elif (i+width>image.shape[0]):
                #slide back over
                patch = np.zeros((width, height, image.shape[2]))
                #patch[0:image.shape[0]-i,0:height] = image[i:image.shape[0], j:j+height]
                patch = image[image.shape[0]-width:image.shape[0], j:j+height]
                #DEBUG
                #remover = np.copy(image)
                #remover[image.shape[0]-width:image.shape[0], j:j+height]=254
                #display_color(remover[:,:,:3].astype(np.uint8))
                #display_color(patch[:,:,:3].astype(np.uint8))
            #check if we went over the y image boundary
            elif (j+height>image.shape[1]):
                #slide back over
                patch = np.zeros((width, height, image.shape[2]))
                #patch[0:width,0:image.shape[1]-j] = image[i:i+width, j:image.shape[1]]
                patch = image[i:i+width, image.shape[1]-height:image.shape[1]]
                #DEBUG
                #remover = np.copy(image)
                #remover[i:i+width, image.shape[1]-height:image.shape[1]]=254
                #print "Displaying patch region"
                #display_color(remover[:,:,:3].astype(np.uint8))
                #display_color(patch[:,:,:3].astype(np.uint8))
            #fine: within image, just get patches
            else:
                patch = image[i:i+width, j:j+height]
                #DEBUG
                #remover = np.copy(image)
                #remover[i:i+width, j:j+width]=254
                #display_color(remover[:,:,:3].astype(np.uint8))
                #display_color(patch[:,:,:3].astype(np.uint8))
            #check that 
            if resolution != finalRes:
                #resize our patch to be correct scale
                #patch = misc.imresize(patch, (finalRes, finalRes), interp='bilinear', mode=None)
                patch = cv2.resize(patch, (finalRes, finalRes))
            patches.append(patch)
            index = index + 1
    return patches#, patchDim

'''
Resize patches to all be the same size? Done in patches to avoid re-iterating :D
'''

'''
Load Images, only here since I keep trading loading libraries
'''
def load_image(filename):
    image = cv2.imread(filename, cv2.IMREAD_UNCHANGED)
    return image

'''
Save Images, similar to above
'''
def save_image(image, filename="default"):
    print "Saving Image"
    #check filename, if default add time
    if filename == "default":
        filename = filename + "_" + str(time.time()) + ".png"
    elif filename[len(filename)-4 : len(filename)] != ".png":
        print "Bad extension: ",filename
        filename = filename + ".png"
    cv2.imwrite(filename, image)#, cv2.CV_16U)#? #IPLImage

'''
Find images
'''
def find_data(directory="data"):
    print "Finding Data"
    #create list with glob
    fileList = []
    #store current location, so we can get back fast
    originalDir = os.getcwd()
    #go to data location
    os.chdir(directory)
    #get current directory's tree
    directoryc = os.getcwd()
    files = []
    #iterate over all branches of tree, collect images
    for dirs, subDirs, filenames in os.walk(directoryc):#check walks correct location
        for item in filenames:
            x = os.path.join(dirs, item)
            y = x.split('/')#take off first 8
            #only collect rgb image names
            if (not "_depth" in y[-1]) and (not "_loc" in y[-1]) and (not "_mask" in y[-1]) and (not "_crop" in y[-1]):
                #print y
                index = y.index(directory)
                y = y[index+1:]
                title =''
                for stuff in y:
                    title = title + stuff + '/'
                title = title[:len(title)-1]
                #print title
                #raw_input('Enter')
                files.append('/'+title)
    #return to previous Directory
    os.chdir(originalDir)
    #return directory and files
    return (files, directoryc)

'''
Get the correct smaller areas to get patches from
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
    return result

'''
Do standard mean calc: Load images, find mean, subtract mean (std patches)
'''
def mean_normalize_images(imageList, mean):
    #subtract mean from images
    centered_images = [image-mean for image in imageList]
    #find patches of images
    patches_centered_images = [find_patches(centered_image, resolution=64, stride=64) for centered_image in centered_images]
    patches_centered_images = [item for sublist in patches_centered_images for item in sublist]
    #create name for save location
    overall = os.getcwd()
    directory = overall+"/StdMeanStdPatch"
    print directory
    emergency_quit()
    #create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    for i,item in enumerate(patches_centered_images):
        if i<50:
            save_image(item, directory+"/image_"+str(i)+".png")

'''
Do standard mean calc: Load images, find mean, subtract mean (multi-res patches)
'''
def mean_normalize_images_multi(imageList, mean):
    #subtract mean from images
    centered_images = [image-mean for image in imageList]
    #find multi-res patches of images
    patches_centered_images = [find_multi_res_patches(centered_image) for centered_image in centered_images]
    patches_centered_images = [item for sublist in patches_centered_images for item in sublist]
    #create name for save location
    overall = os.getcwd()
    directory = overall+"/StdMeanMultiPatch"
    print directory
    emergency_quit()
    #create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    for i,item in enumerate(patches_centered_images):
        if i<50:
            save_image(item, directory+"/image_"+str(i)+".png")

'''
Do non-standard mean calc: Load Images, find mean, find patches, find mean patch, subtract mean patch?
'''
def mean_normalize_image_patches(imageList, mean):
    #find patches of images
    patches_images = [find_patches(image, resolution=64, stride=64) for image in imageList]
    patches_images = [item for sublist in patches_images for item in sublist]
    #find patches of mean
    patches_mean = find_patches(mean)
    #find mean of patches
    patch_mean = find_mean(patches_mean)
    #subtract mean patch from image patches
    centered_patches_images = [patch-patch_mean for patch in patches_images]
    #create name for save location
    overall = os.getcwd()
    directory = overall+"/PatchMeanStdPatch"
    print directory
    emergency_quit()
    #create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    for i,item in enumerate(centered_patches_images):
        if i<50:
            save_image(item, directory+"/image_"+str(i)+".png")

'''
Do non-standard mean calc: Load Images, find mean, find multi-resolution patches, find mean patch, subtract mean patch?
'''
def mean_normalize_image_multi_patches(imageList, mean):
    #find multi-res patches of images
    patches_images = [find_multi_res_patches(image) for image in imageList]
    patches_images = [item for sublist in patches_images for item in sublist]
    #find multi-res patches of mean
    patches_mean = find_multi_res_patches(mean)
    #find mean of patches
    patch_mean = find_mean(patches_mean)
    #subtract mean patch from image patches
    centered_patches_images = [patch-patch_mean for patch in patches_images]
    #create name for save location
    overall = os.getcwd()
    directory = overall+"/PatchMeanMultiPatch"
    print directory
    emergency_quit()
    #create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    for i,item in enumerate(centered_patches_images):
        if i<50:
            save_image(item, directory+"/image_"+str(i)+".png")

if __name__ == "__main__":
    data_loc="data"
    #find images
    files, directory = find_data(data_loc)
    #load images
    imageList = []
    crop_boxes = []
    crop_overall = [999,999,-1,-1]
    for filename in files:
        mask = load_image(directory+filename[:len(filename)-4]+"_mask.png")
        if mask != None:
            crop_boxes.append(get_crop_box(mask))
            imageList.append(load_image(directory+filename))
            #Check max and min
            if crop_overall[2] < crop_boxes[-1][2]:
                crop_overall[2] = crop_boxes[-1][2]
            if crop_overall[3] < crop_boxes[-1][3]:
                crop_overall[3] = crop_boxes[-1][3]
            if crop_overall[0] > crop_boxes[-1][0]:
                crop_overall[0] = crop_boxes[-1][0]
            if crop_overall[1] > crop_boxes[-1][1]:
                crop_overall[1] = crop_boxes[-1][1]
    #find mean of images
    mean  = find_mean(imageList)
    mean = mean[crop_overall[0]:crop_overall[2],crop_overall[1]:crop_overall[3]]

    #check that image cropping indices are correct:
    '''
    image = imageList[0]
    display_color(image[0:crop_overall[0],0:image.shape[1],:])
    display_color(image[crop_overall[0]:crop_overall[2],0:crop_overall[1],:])
    display_color(image[crop_overall[0]:crop_overall[2],crop_overall[3]:image.shape[1],:])
    display_color(image[crop_overall[2]:image.shape[0],0:image.shape[1],:])
    display_color(image[crop_overall[0]:crop_overall[2],crop_overall[1]:crop_overall[3],:])
    '''

    #apply overall crop for now:
    imageList = [image[crop_overall[0]:crop_overall[2],crop_overall[1]:crop_overall[3]] for image in imageList]
    #mean_normalize_images(imageList, mean)
    #mean_normalize_image_patches(imageList, mean)
    #mean_normalize_images_multi(imageList, mean)
    #mean_normalize_image_multi_patches(imageList, mean)
    #So: we want to see about the mean subtract and add, with reshaping as in convnet.

    #check that image cropping indices are correct: Single image first, list next
    '''
    #how we prepare the data for training:
    #flatten data, keep channels in order
    data = n.asarray([(sample.astype(n.float32, order='C')).flatten('F') for sample in data])
    #need to flatten the data and swap axis order: data x numSamples
    data = n.require(n.swapaxes(data, 0, 1), dtype=n.single, requirements='C')
    '''
    #grab image
    image = imageList[0].astype(np.single)
    mean = mean.astype(np.single)
    print "Original Shape ",image.shape
    display_color(image)
    display_color(image-mean)
    display_color((image-mean)+mean)
    #process as above
    image = ((image-mean).astype(np.float32, order='C')).flatten('F')
    print "Flattened Shape ",image.shape
    image = np.require(image, dtype=np.single, requirements='C')
    #attempt to reconstruct
    image = image.reshape(imageList[0].shape[2], imageList[0].shape[1], imageList[0].shape[0]).swapaxes(0,2)
    print image.shape
    #compare original and reconstruction
    display_color(imageList[0].astype(np.single))
    display_color(image+mean)
    #Above is correct: images appear strange due to np.single type
    '''
    #how we reconstruct the data after training:
    data = (data.T.reshape(data.shape[1], self.num_colors, self.final_size, self.final_size).swapaxes(1,3)) / 255.0
    #return n.require(data+self.mean_patch, dtype=n.single)[:,:,:,:3]
    #[:,:,:,::-1]
    return n.require(data, dtype=n.single)[:,:,:,:3]
    '''
    data = np.asarray([(sample.astype(np.single, order='C')).flatten('F') for sample in imageList])
    print data.shape
    data = np.require(np.swapaxes(data, 0, 1), dtype=np.single, requirements='C')
    #now reconstruct
    data = (data.T.reshape(len(imageList), imageList[0].shape[2], imageList[0].shape[1], imageList[0].shape[0]).swapaxes(1,3))
    print data.shape
    #display
    display_color(imageList[0].astype(np.single))
    display_color(data[0])

    #attempt above with list of images: to match convnet mroe closely

    sys.exit()