import sys, os, platform
import time
import ctypes
from primesense import openni2
from primesense import _openni2 as c_api
import numpy.random as nr
import numpy as np
#temporary for checking display:
#import matplotlib.pyplot as plt
#from PIL import Image
#PIL Cannot store uint16 images
#however, opencv does BGR order...
import cv2

# add to sys.path: my two versions of openni.
#Recommended that ou build your own: this is ubuntu x64 and arch x64, but they may not work on similar systems.
print "Sys setup ",os.name,',',platform.system(),',',platform.release()
for item in sys.path:
    print item

if "ARCH" in platform.release():
    print "Running on Arch "
    sys.path.append(sys.path[0]+"/arch-linux")
else:
    sys.path.append(sys.path[0]+"/ubuntu-linux")
    
for item in sys.path:
    print item

class PrimesenseSnapshots:
    def __init__(self):
        print "Initializing"
        self.size = 'full'
        self.stream_type = 'both' #for now this does nothing
        self.streaming = False
        self.depth_pixel_type = c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM
        self.color_pixel_type = c_api.OniPixelFormat.ONI_PIXEL_FORMAT_RGB888
        self.setup_camera()

    def setup_camera(self):
        print "Setup"
        #initialize the camera
        openni2.initialize(sys.path[-1]) #this only works because we added our openni path just now
        #AND/OR initialize niTE? (also inits openni)
        #find device
        self.device = openni2.Device.open_any()
        #maybe better error checker available
        if not self.device:
            print "Error finding device. Check OpenNi docs."
            sys.exit();

        #debugging: print the options: pixel types, resolutions
        #self.print_video_options(self.device, openni2.SENSOR_DEPTH)
        #self.print_video_options(self.device, openni2.SENSOR_COLOR)

        #make sure color and depth are synced, why would we not want this? If we're only grabbing one.
        print "Syncing"
        if not self.device.get_depth_color_sync_enabled():
            self.device.set_depth_color_sync_enabled(True)

        #also: registration mode: could not find parameters that worked here...
        #print "Supported? ",self.device.is_image_registration_mode_supported(openni2.IMAGE_REGISTRATION_DEPTH_TO_COLOR) # This works, follwoing do not
        #self.device.get_image_registration_mode() # this fails: bad_parameter? but it takes no parameters?
        #self.device.set_image_registration_mode(openni2.IMAGE_REGISTRATION_DEPTH_TO_COLOR) # this also fails

        #create both streams: perhaps this should be done later, close to Start of streaming
        print "Making Streams"
        self.depth_stream = self.device.create_depth_stream()
        self.color_stream = self.device.create_color_stream()
        #Get maxes and mins
        print "Find depth range"
        #self.max_depth = self.depth_stream.get_max_pixel_value()
        #self.min_depth = self.depth_stream.get_min_pixel_value()
        #
        #self.max_color = self.color_stream.get_max_pixel_value()
        #self.min_color = self.color_stream.get_min_pixel_value()
        #print "Depth Max and Min ",self.max_depth,',',self.min_depth
        #print "Color Max and Min ",self.max_color,',',self.min_color

        #set pixel format and resolution for both streams
        print "Setting Resolution"
        if self.size == 'quarter':
            self.depth_stream.set_video_mode(c_api.OniVideoMode(pixelFormat = self.depth_pixel_type, resolutionX = 320, resolutionY = 240, fps = 30))
            self.color_stream.set_video_mode(c_api.OniVideoMode(pixelFormat = self.color_pixel_type, resolutionX = 320, resolutionY = 240, fps = 30))
        elif self.size == 'full':
            #print "Using full size"
            self.depth_stream.set_video_mode(c_api.OniVideoMode(pixelFormat = self.depth_pixel_type, resolutionX = 640, resolutionY = 480, fps = 30))
            self.color_stream.set_video_mode(c_api.OniVideoMode(pixelFormat = self.color_pixel_type, resolutionX = 640, resolutionY = 480, fps = 30))
        else:
            print "No recognizeable video resolution given, defaulting to QVGA ('quarter')"
            self.depth_stream.set_video_mode(c_api.OniVideoMode(pixelFormat = self.depth_pixel_type, resolutionX = 320, resolutionY = 240, fps = 30))
            self.color_stream.set_video_mode(c_api.OniVideoMode(pixelFormat = self.color_pixel_type, resolutionX = 320, resolutionY = 240, fps = 30))
        #return for now, start stream later when we begin testing: ie: get_batch(test=true):if test_has_been==false

    def begin(self):
        print "Starting Streams"
        #begin streams
        self.depth_stream.start()
        self.color_stream.start()
        time.sleep(0.4)
        #mark as running
        self.streaming = True

    '''
    This function is meant to collect a frame, display it, and ask 
    the user if they want to save it, or not. Also checks if they 
    want to quit.
    '''
    def collect(self):
        print "Collecting"
        #assume setup and begin already called
        #THIS WILL BE A LOOP ONCE IT IS TESTED
        #wait for frame
        print "Waiting for Color Stream"
        openni2.wait_for_any_stream([self.color_stream])
        print "Waiting for Depth Stream"
        openni2.wait_for_any_stream([self.depth_stream])
        #read frame
        print "Reading Stream"
        frame_color = self.color_stream.read_frame()
        frame_depth = self.depth_stream.read_frame()
        #translate to numpy
        print "Get data"
        frame_data_depth = frame_depth.get_buffer_as(ctypes.c_uint16)#pixel values...may change?
        frame_data_color = frame_color.get_buffer_as(ctypes.c_uint8)
        #conversion from uint16 to uint8...hmm
        print "Reshaping"
        depthData  = (np.frombuffer(frame_data_depth, dtype=np.uint16)).astype(dtype=np.uint16, order='C')
        colorData  = (np.frombuffer(frame_data_color, dtype=np.uint8)).astype(dtype=np.uint8, order='C')
        depthData = self.reshape(depthData)
        colorData = self.reshape(colorData)
        #display frame
        print "Displaying"
        self.display_color(colorData)
        self.display_depth(depthData)
        #DEBUG
        self.test_save_and_load(depthData)
        self.test_uint8_vs_uint16(colorData)
        #ask user for choice
        choice = self.emergency_quit()
        #save or drop or quit
        if choice == 's':
            #get base filename?
            timer = time.time()
            self.save_image(depthData[:,::-1,:], "default_"+str(timer)+ "_depth.png")
            self.save_image(colorData[:,::-1,::-1], "default_"+str(timer)+ ".png")
        #else we just drop it and continue

    def save_image(self, image, filename="default"):
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

    def load_image(self, filename):
        #in case we need this function
        img = cv2.imread(filename, cv2.IMREAD_UNCHANGED)
        return img
        
    def end(self):
        print "Ending Streams"
        if self.streaming:
            self.depth_stream.stop()
            self.color_stream.stop()

    def close(self):
        print "Closing Streams"
        self.end()
        openni2.unload()

    '''
    The folowing are all display/debug functions
    '''
    def display_color(self, image, brief = False):
        print "Displaying color"
        #plt.imshow(image.astype(np.uint8))
        #if brief:
        #    plt.pause(.1)
        #    plt.draw()
        #else:
        #    plt.show()
        #plt.close()
        cv2.imshow('Color',image[:,::-1,::-1])
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def display_depth(self, depth, brief = False):
        print "Displaying Depth"
        #depth is width x height x 1
        #scale values: not needed with opencv
        #temp = self.scale_stack_depth(depth)
        #plt.imshow(temp.astype(np.uint8))
        #if brief:
        #    plt.pause(.1)
        #    plt.draw()
        #else:
        #    plt.show()
        #plt.close()
        print depth.shape
        cv2.imshow('Depth',depth)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def scale_stack_depth(self, img):
        print "Scaling and Stacking"
        #scale so max is 255
        if hasattr(self, 'max_depth'):
            newImg = (img.astype(np.float32)*(255.0/self.max_depth)).astype(np.uint16)
        else:
            #find max and min
            i,j,k = np.unravel_index(img.argmax(), img.shape)
            a,b,c = np.unravel_index(img.argmin(), img.shape)
            newImg = (img.astype(np.float32)*(255.0/img[i,j,k])).astype(np.uint16)
        #shape it accordingly (depth weird order)
        newImg = np.concatenate((newImg, newImg, newImg), axis=0)
        newImg = np.swapaxes(newImg, 0, 2)
        newImg = np.swapaxes(newImg, 0, 1)
        return newImg

    def scale_stack_depth_out(self, img):
        print "Scaling and Stacking without outlier (just to make it obvious)"
        #find max and min
        i,j,k = np.unravel_index(img.argmax(), img.shape)
        a,b,c = np.unravel_index(img.argmin(), img.shape)
        #print "Depth ",img[i,j,k],',',img[a,b,c]
        #get second max, if far apart, use second max instead (outlier/special value max)
        tempCheck = img
        tempCheck[tempCheck == img[i,j,k]] = 100#newImg[a,b,c]
        tempCheck[tempCheck == img[a,b,c]] = 100
        i2,j2,k2 = np.unravel_index(tempCheck.argmax(), tempCheck.shape)
        a2,b2,c2 = np.unravel_index(tempCheck.argmin(), tempCheck.shape)
        #print "Depth ",img[i2,j2,k2],',',img[a2,b2,c2]
        img[img == img[i,j,k]] = img[i2,j2,k2]
        img[img == img[a,b,c]] = img[a2,b2,c2]
        #scale so max is 255
        #print "Changing "," into "
        newImg = (img.astype(np.float32)*(255.0/img[i2,j2,k2])).astype(np.uint8)

        #shape it accordingly (depth weird order)
        newImg = np.concatenate((newImg, newImg, newImg), axis=0)
        newImg = np.swapaxes(newImg, 0, 2)
        newImg = np.swapaxes(newImg, 0, 1)
        return newImg

    def reshape(self, img):
        print "Reshaping"
        assert len(img.shape) == 1, "Image Shape is Multi-Dimensional before reshaping "+str(img.shape)
        whatisit = img.shape[0]
        #print "Initial Size in reshape ",whatisit
        if whatisit == (640*480*1):
            #Full Size Depth
            img.shape = (1, 480, 640)
            #This order? Really? ^
            img = np.swapaxes(img, 0, 2)
            img = np.swapaxes(img, 0, 1)
            #img = scale_stack_depth_out(img)
        elif whatisit == (640*480*3):
            #Full Size Color
            img.shape = (480, 640, 3)
            #these are, what is it, normalizsed?
        elif whatisit == (1280*1024*3):
            #Giant Color (not depth available)
            img.shape = (1024, 1280, 3)
        elif whatisit == (1280*1024*1):
            #Depth High res: not possible on current camera
            #this should not be possible with this camera
            img.shape = (1, 1024, 1280)
            img = np.swapaxes(img, 0, 2)
            img = np.swapaxes(img, 0, 1)
            #img = scale_stack_depth_out(img)
        elif whatisit == (320*240*1):
            #Quarter size depth
            img.shape = (1, 240, 320)
            img = np.swapaxes(img, 0, 2)
            img = np.swapaxes(img, 0, 1)
            #img = scale_stack_depth_out(img)
        elif whatisit == (320*240*3):
            #Quarter Size Color
            img.shape = (240, 320, 3)
        else:
            print "Frames do not match any image format. Frames are of size: ",img.size
            sys.exit()
        #print "Final size in reshape ",img.shape
        return img

    '''
    Prints the debugging data: device options
    '''
    def print_video_options(self, device, streamType):
        print "Options:"
        stream_info = self.device.get_sensor_info(streamType)
        print "Stream format options: ", streamType
        for item in stream_info.videoModes:
            print item

    def emergency_quit(self):
        print "Select q to quit, s to save, otherwise "
        s = raw_input('--> ')
        if s=='q':
            self.end()
            self.close()
            sys.exit()
        else:
            return s

    def test_save_and_load(self, depth):
        #grab depth frame from camera
        print "Depth Type ",depth.dtype
        #save
        self.save_image(depth, "tempDepthTest.png")
        #load
        img = self.load_image("tempDepthTest.png")
        #check that values are unchanged (still uint16)
        print "After Load: ",img.dtype
        assert type(depth) == type(img), "Types of depth and image are not the same "+str(type(depth))+','+str(type(img))
        assert depth.dtype == img.dtype, "dtypes of depth and img are not the same "+str(depth.dtype)+','+str(img.dtype)
        assert depth.shape[0] == img.shape[0], "x Shapes of depth and image are not the same "+str(depth.shape)+','+str(img.shape)
        assert depth.shape[1] == img.shape[1], "y Shapes of depth and image are not the same "+str(depth.shape)+','+str(img.shape)

    def test_uint8_vs_uint16(self, color):
        print "Color Type",color.dtype
        #display
        self.display_color(color)
        #try swapping into uint16
        colorRe = np.copy(color)
        colorRe.astype(np.uint16)
        #test values
        print np.all(np.equal(color, colorRe)) #may cause type error...or not. Numpy is strange
        #display
        self.display_color(colorRe)
        #try swapping back to uint8
        colorRe.astype(np.uint8)
        #test
        print np.all(np.equal(color, colorRe))
        #display
        self.display_color(colorRe)


if __name__ == "__main__":
    snapper = PrimesenseSnapshots()
    snapper.begin()
    snapper.collect()
