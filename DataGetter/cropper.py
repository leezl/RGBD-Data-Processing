'''
openni data cropper

Because the original was destoryed in a terrible accident. never ever reset hard.
dual langauge
'''

import sys, os
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

#cropImages:
def cropImages(): 
    #find all directories
    directories = [ name for name in os.listdir('.') if os.path.isdir(os.path.join('.', name)) ]
    #for each directory:
    for directory in directories:
        #find all images which do not already have crop
        for filename in os.listdir(directory):
            #print "file name: ",filename
            #emergency_quit()
            #print os.path.isfile(filename[:-4]+"_crop.txt")
            if re.match('^.*[0-9]+\.png$', filename) and not (os.path.isfile(os.path.join(directory,filename[:-4]+"_crop.txt"))):
                #create crop storage
                crop = [0,0,479,639]#check order
                #chekc done
                done = False
                #for each image:
                print "matching filename ",filename
                print os.path.join(directory,filename)
                #load image
                img=mpimg.imread(os.path.join(directory,filename))
                print img.shape
                print img[0,0,0]
                while not done:
                    #display image
                    display_image(img)
                    #get crop value
                    crop[0], crop[1] = [int(x) for x in (raw_input('Enter Low Numbers: ')).split(' ')]#does this work...?
                    #flip y axis...because matplot is stupid
                    #crop[2] = img.shape[0]-crop[2]
                    #crop[1] = img.shape[1]-crop[1]
                    crop[2], crop[3] = [int(x) for x in (raw_input('Enter High Numbers: ')).split(' ')]#does this work...?
                    #crop[0] = img.shape[0]-crop[0]
                    #crop[3] = img.shape[1]-crop[3]
                    #display crop
                    print "crop values: ",crop
                    display_image_with_crop(img, crop)
                    #ask for corrections
                    if raw_input('Done? (s)') == 's':
                        done = True
                        print "cropped filename: ",filename[:-4]+'_crop.txt'
                        #save crop value to file
                        f = open(os.path.join(directory,filename[:-4]+"_crop.txt"),'w')
                        f.write(str(crop[0])+' '+str(crop[1])+' '+str(crop[2])+' '+str(crop[3]))
                        f.close()

#display image
def display_image(image, brief=False):
    #use matplot lib here, just because it lets us see grid position of mouse
    plt.imshow(image)
    if brief:
        plt.pause(.1)
        plt.draw()
    else:
        plt.show()
    plt.close()

#display image
def display_image_with_crop(image, crop, brief=False):
    #use matplot lib here, just because it lets us see grid position of mouse
    img = np.copy(image)
    for i in range(crop[0]+1, crop[2]-1):
        img[crop[1]+1, i] = (1,0,0)
        img[crop[3]-1, i] = (1,0,0)
    for i in range(crop[1]+1, crop[3]-1):
        img[i, crop[0]+1] = (1,0,0)
        img[i, crop[2]-1] = (1,0,0)
    display_image(img)

def emergency_quit():
    print "Select q to quit, s to save, otherwise "
    s = raw_input('--> ')
    if s=='q':
        sys.exit()
    else:
        return s


if __name__ == "__main__":
    cropImages()