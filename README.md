RGBD-Data-Processing
====================

A collection of python files I use for rearranging RGBD data: finding the mean, zipping batches, creating reflected versions, grabbing images from a camera. Specifically this was created to feed into the Cuda-Convnet code, creating batches and Meta data of the batches, as well as object labels based on the filenames (apple_1_1_1.png)

The DataGetter folder contains code designed to pull images from the Kinect and primesense cameras.

The original folder, contains the RGBD dataset and code for processing it.

The pickledGZIP data contains the pickled and zipped RGBD data batches produced by the code here.

The TestTar folder was created to contain a much smaller amoutn of data during writing of the data processing code, so that if there were errors made the actual data folders would not be deleted. Test code should not leave this fodler until it has been properly tested for safety.

The files rgbdPickled____.py are all versions of code which find the RGBD data and move it into pickled batches, while calculating crop boxes, the mean of the data, and labels (of objects). rgbdPickleGZipLabv2 is the most recent, the others are missing features: No GZip, doesn't allow interrruption, does not create the meta.batch file.


At some poibnt this was completely deleted and was not under version control, which is why there are three versions of everything. Cleaning is incomplete.

