'''
This is intended to prepare the data for processing using Caffe. 
Caffe expects a leveldb data format, where each image has a single 
label and is already the size and shape we are using for training. 
We need to provide a list of files and labels. If we want to use a 
camera though, we'll need to be able to pull our patches out of 
images as we are running. So:

Initial Version: Find images (whole) and labels (from files)
use thr
'''