#need to compare cloud and range images quickly....yeah
#640 x 480
#utility functions
import sys
#file path checking: os.path.isfile('')
import os
import numpy

def loadCloud(filename):
    try:
        f = open(filename)
    except IOError:
        print "Error loading file list...", sys.exc_info()[0]
    else:
        lines = f.readlines()
        cloud = []
        for line in lines:
            #print line
            #raw_input('-')
            #split into nums, load into array, load array into list, numpy it
            points = line.split()# (x,y,z - r,g,b,a)
            pointArray = numpy.zeros((7))#7
            for point in points:#(x,y,z or - or r,g,b,a)
                #print point
                #raw_input('-')
                point = point.strip('()')
                if point[0] == '-':
                    pass
                else:
                    value=point.split(',')
                    #print value
                    #raw_input('-')
                    if len(value) == 3:
                        pointArray[0]=float(value[0])
                        pointArray[1]=float(value[1])
                        pointArray[2]=float(value[2])
                    else:
                        pointArray[3]=float(value[0])
                        pointArray[4]=float(value[1])
                        pointArray[5]=float(value[2])
                        pointArray[6]=float(value[3])
            #print pointArray
            cloud.append(pointArray)
    print len(cloud), ' ', 640*480
    return cloud

def loadRangeImage(filename):
    try:
        f = open(filename)
    except IOError:
        print "Error loading file list...", sys.exc_info()[0]
    else:
        lines = f.readlines()
        rangeImage = []
        height=0
        width=0
        
        for line in lines:
            if line[0] == 'H':
                words = line.split()
                height = int(words[1])
                width = int(words[3])
            elif line[0] == 'E':
                pass
            else:
                #print line
                #raw_input('-line-')
                #split to nums, load to array, load array to list, numpy it
                point = line.replace(',','')
                #print point
                #raw_input('-point-')
                points = point.split()# x y z r x y
                pointArray = numpy.zeros((6))#6
                #print points
                #raw_input('-points-')
                pointArray[0]=float(points[0])
                pointArray[1]=float(points[1])
                pointArray[2]=float(points[2])
                pointArray[3]=float(points[3])
                pointArray[4]=float(points[4])
                pointArray[5]=float(points[5])
                #print pointArray
                rangeImage.append(pointArray)
    return height, width, rangeImage

def compare(filename):#so, cloud x,y,z has nothing to do with range x,y,z
    cloud = loadCloud(filename+"Cloud")# x y z r g b a
    rangeImage = loadRangeImage(filename)# x y z r x y
    #compare first 3 values...
    same = True
    for item in rangeImage:#range image is smaller?
        localSame = False
        for point in cloud:
            if item[0]==point[0] and item[1] == point[1] and item[2] == point[2]:
                same=True
            else:
                pass
        if localSame == False:
            same = False
            break
    print "Result: ", same


def makeImagefromRange(filename):
    try:
        f = open(filename)
    except IOError:
        print "Error loading file list...", sys.exc_info()[0]
    else:
        lines = f.readlines()
        line = lines[0]
        words = line.split()
        height = int(words[1])
        width = int(words[3])
        image = numpy.zeros((height,width))
        height=0
        width=0
        
        for line in lines:
            if line[0] == 'H':
                pass
            elif line[0] == 'E':
                pass
            else:
                #print line
                #raw_input('-line-')
                #split to nums, load to array, load array to list, numpy it
                point = line.replace(',','')
                #print point
                #raw_input('-point-')
                points = point.split()# x y z r x y
                pointArray = numpy.zeros((6))#6
                #print points
                #raw_input('-points-')
                pointArray[0]=float(points[0])
                pointArray[1]=float(points[1])
                pointArray[2]=float(points[2])
                pointArray[3]=float(points[3])
                pointArray[4]=float(points[4])
                pointArray[5]=float(points[5])
                #print pointArray
                image[pointArray[4], pointArray[5]] = pointArray[3]
    return image

def makeImagefromCloud():#incomplete
    try:
        f = open(filename)
    except IOError:
        print "Error loading file list...", sys.exc_info()[0]
    else:
        lines = f.readlines()
        cloud = numpy.zeros((640, 480))
        for line in lines:
            #print line
            #raw_input('-')
            #split into nums, load into array, load array into list, numpy it
            points = line.split()# (x,y,z - r,g,b,a)
            pointArray = numpy.zeros((7))#7
            for point in points:#(x,y,z or - or r,g,b,a)
                #print point
                #raw_input('-')
                point = point.strip('()')
                if point[0] == '-':
                    pass
                else:
                    value=point.split(',')
                    #print value
                    #raw_input('-')
                    if len(value) == 3:
                        pointArray[0]=float(value[0])
                        pointArray[1]=float(value[1])
                        pointArray[2]=float(value[2])
                    else:
                        pointArray[3]=float(value[0])
                        pointArray[4]=float(value[1])
                        pointArray[5]=float(value[2])
                        pointArray[6]=float(value[3])
            #print pointArray
            #cloud.append(pointArray)
    return cloud


if __name__ == "__main__":
    cloud = loadCloud('pics/testCloud')
    rangeImage = loadRangeImage('pics/test')
    #makeImagefromRange('pics/test')
    sys.exit(0)
