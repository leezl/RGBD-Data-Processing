/*
Attempt to create images from 3d data from kinect. Use pcl/openni to pull clouds. Set all parameters in Viewer, so we see output, then grab clouds.

Magick++ is used for making .png images of the point cloud, and can be removed as a dependency if you don't need that.

openniViewer
kinectMotor
are the only two files in this directory that are needed for this program. The others are there for reference to the original tutorials.
*/
#include <iostream>
#include "openniViewer.cpp"
#include "kinectMotor.cpp"
#include <pcl/range_image/range_image.h>
#include <pcl/impl/point_types.hpp>
#include <pcl/visualization/range_image_visualizer.h>
#include <Magick++.h>
////////////////
#include <boost/thread/thread.hpp>
#include <pcl/common/common_headers.h>
#include <pcl/common/common_headers.h>
#include <pcl/visualization/pcl_visualizer.h>
#include <pcl/console/parse.h>

int menuLoop(int argc, char ** argv);
void cloudToImage(pcl::PointCloud<pcl::PointXYZRGBA>::Ptr cloud, std::string filename);

int main (int argc, char *argv[])
{
    return menuLoop(argc, argv);
}

/////////////////////////////////////

/*
menuLoop()
input: command line arguments
output: none
needs: standard output, pcl dependencies
process: Displays the menu and accepts input. Begins other processes.
*/
int menuLoop(int argc, char ** argv){
    int input=-1;
    pcl::PointCloud<pcl::PointXYZRGBA>::Ptr snapshot (new pcl::PointCloud<pcl::PointXYZRGBA>);
    bool haveCloud=false, enableMotor=true;
    std::string file="";
    //create viewer by default
    SimpleOpenNIViewer viewer; //to display and process everything
    KinectMotor motors; //to move the Kinect
    int kinectLevel=0;
    float near=0.0, up=0.0, far=0.0, down=0.0, left=0.0, right=0.0, val = 0.0;

    Magick::InitializeMagick(*argv);////Image code to be removed if no MAGICK
    
    if (!motors.Open())
	{
	    std::cout<<"Motors not active..."<<std::endl;
	    enableMotor=false;
	} else{
	    motors.Move(0);
	}
    
    while(input != 9){
        std::cout<<std::endl<<"Options: "<<std::endl;
        std::cout<<"0 View point cloud stream"<<std::endl;
        std::cout<<"1 Grab single cloud"<<std::endl;
        std::cout<<"2 Depth Filter cloud"<<std::endl;
        std::cout<<"3 Height Filter cloud"<<std::endl;
        std::cout<<"4 Width Filter cloud"<<std::endl;
        std::cout<<"5 Plane Removal filter"<<std::endl;
        std::cout<<"6 Make image"<<std::endl;
        std::cout<<"7 Lower Kinect"<<std::endl;
        std::cout<<"8 Raise Kinect"<<std::endl;
        std::cout<<"9 Exit"<<std::endl;
        std::cin>>input;        
        switch(input){
            case 0:
                std::cout<<"Displaying Cloud..."<<std::endl;
                //call display function
                viewer.display();
                break;
            case 1:
                std::cout<<"Grabbing a cloud..."<<std::endl;
                //get a cloud
                snapshot = viewer.getCloud();
                haveCloud=true;
                break;
            case 2:
                //check if receiving cloud
                std::cout<<"Depth filter cloud..."<<std::endl;
                near=far=0.0;
                while(near>=far)
                {
                    std::cout<<"Enter near value: ";
                    std::cin>>near;
                    std::cout<<std::endl<<"Enter far value: ";
                    std::cin>>far;
                    if(near>=far)
                    {
                        std::cout<<"Near shouldn't be greater than far..."<<std::endl;
                    }
                }
                //set filter
                viewer.setDepthFilter(near,far);
                break;
            case 3:
                //check if receiving cloud
                std::cout<<"Height filter cloud..."<<std::endl;
                up=down=0.0;
                while(down>=up)
                {
                    std::cout<<"Enter down value: ";
                    std::cin>>down;
                    std::cout<<std::endl<<"Enter up value: ";
                    std::cin>>up;
                    if(down>=up)
                    {
                        std::cout<<"Down shouldn't be greater than up..."<<std::endl;
                    }
                }
                //set filter
                viewer.setHeightFilter(down,up);
                break;
            case 4:
                //check if receiving cloud
                std::cout<<"Width filter cloud..."<<std::endl;
                right=left=0.0;
                while(left>=right)
                {
                    std::cout<<"Enter left value: ";
                    std::cin>>left;
                    std::cout<<std::endl<<"Enter right value: ";
                    std::cin>>right;
                    if(left>=right)
                    {
                        std::cout<<"Left shouldn't be greater than right..."<<std::endl;
                    }
                }
                //set filter
                viewer.setWidthFilter(left,right);
                break;
            case 5:
                std::cout<<"Removing large planes..."<<std::endl;
		        std::cout<<"Enter planar distance: (0.01 to 0.05) ";
		        std::cin>>val;
                viewer.setTableFilter(val);
                break;
            case 6:
                std::cout<<"Making image..."<<std::endl;
                //Check if have cloud
                if(haveCloud && !snapshot->empty())
                {
                    cout<<"Enter a filename: ";
                    std::string filename;
                    cin>>filename;
                    //attempt image conversion
                    cloudToImage(snapshot, filename);
                }
                else
                {
                    //print warning
                    std::cout<<"No still cloud to work on..."<<std::endl;
                }
                break;
	        case 7:
		        std::cout<<"Lowering Kinect..."<<std::endl;
		        if(enableMotor){
		            kinectLevel=kinectLevel-5;
		            motors.Move(kinectLevel);
		        }
		        break;
	        case 8:
		        std::cout<<"Raising Kinect..."<<std::endl;
		        if(enableMotor){
		            kinectLevel=kinectLevel+5;
		            motors.Move(kinectLevel);
		        }
		        break;
            /*//Load PointCloud option
            case 9:
                std::cout<<"Loading Data..."<<std::endl;
                std::cout<<"Enter filename: ";
                std::cin>>file;
                snapShot = loadCloudFrom(file);
                haveCloud=true;
            */
            case 9:
                //Exit
                //close everything?
                motors.Move(0);
                return 0;
            default:
                std::cout<<"Bad input value."<<std::endl;
                break;
        }
    }
    motors.Move(0);
    return 0;
}

/*
cloudToImage()
input:
output:
needs:
process: Creates a depth, then flat image from the data. Gets depth, then sets infinite points to white....? difficult part here...
*/

//This is a visualizer helper function, for range Images
void 
setViewerPose (pcl::visualization::PCLVisualizer& viewer, const Eigen::Affine3f& viewer_pose)
{
  Eigen::Vector3f pos_vector = viewer_pose * Eigen::Vector3f(0, 0, 0);
  Eigen::Vector3f look_at_vector = viewer_pose.rotation () * Eigen::Vector3f(0, 0, 1) + pos_vector;
  Eigen::Vector3f up_vector = viewer_pose.rotation () * Eigen::Vector3f(0, -1, 0);
  viewer.setCameraPosition (pos_vector[0], pos_vector[1], pos_vector[2],
                            /*look_at_vector[0], look_at_vector[1], look_at_vector[2],//Don't use LookAt?*/
                            up_vector[0], up_vector[1], up_vector[2]);
}

void cloudToImage(pcl::PointCloud<pcl::PointXYZRGBA>::Ptr cloud, std::string filename)
{
    //save to file
    //initialize image to be 
    Magick::Image my_image("640x480", "white"); // start with creating a white-background canvas
    //Can we store depth in alpha channel, or do we need a separate image? Does it force range? 0-1?
    Magick::Image my_depth("640x480", "white");
    float max_depth=8.0;
    for(int i=0; i<(*cloud).width; i++)
    {
        for(int j=0; j<(*cloud).height; j++){
            pcl::PointXYZRGBA point = (*cloud).at(i,j);
            /*if (!(point.x!=point.x)){//(numeric_limits<float>::quiet_NaN()){
                std::cout<<"Image XY: "<<i<<','<<j<<std::endl;
                std::cout<<"Cloud XYZ: "<<point.x<<' '<<point.y<<' '<<point.z<<std::endl;
                std::cout<<"Cloud RGB: "<<int(point.r)<<' '<<int(point.g)<<' '<<int(point.b)<<std::endl;
            }*/
            if(int(point.r)>255 || int(point.g)>255 || int(point.b)>255){std::cout<<"Bad color Values"<<std::endl;}
            if((point.x==0.0 && point.y==0.0 && point.z==0.0) || (point.x!=point.x || point.y!=point.y && point.z!=point.z))
            {
                my_image.pixelColor(i,j,Magick::ColorRGB(1.0,1.0,1.0));
                my_depth.pixelColor(i,j,Magick::ColorGray(0.0));
            } else{
                my_image.pixelColor(i,j,Magick::ColorRGB(double(int(point.r))/255.0,double(int(point.g))/255.0,double(int(point.b))/255.0));
                my_depth.pixelColor(i,j,Magick::ColorGray(point.z/max_depth));
            }
        }
        my_image.write("../pics/"+filename+s+".png");
        my_depth.write("../pics/"+filename+s+"_depth.png");
    }

}

/*The follwing was in the saving function. May need range images later...
//Note:
  //void 	pcl::io::savePNGFile (const std::string &file_name, const pcl::PointCloud< T > &cloud)
  //pcl::io::savePNGFile("pics/"+filename, *cloud);//should be color, check location of save

//if we want range as the 4th item in a point, we'll need to write our own:bgein with the following:

  //float angularResolution = (float) ( 0.08f * (M_PI/180.0f));  //   1.0 degree in radians//.08 is good, 1.0 is thumbnail
  //float maxAngleWidth     = (float) (360.0f * (M_PI/180.0f));  // 360.0 degree in radians
  //float maxAngleHeight    = (float) (180.0f * (M_PI/180.0f));  // 180.0 degree in radians
  //Eigen::Affine3f sensorPose = (Eigen::Affine3f)Eigen::Translation3f(0.0f, 0.0f, 0.0f);
  //pcl::RangeImage::CoordinateFrame coordinate_frame = pcl::RangeImage::CAMERA_FRAME;
  //float noiseLevel=0.00;
  //float minRange = 0.0f;
  //int borderSize = 1;
  //boost::shared_ptr<pcl::RangeImage> range_image_ptr(new pcl::RangeImage);
  //pcl::RangeImage& range_image = *range_image_ptr;   
  range_image.createFromPointCloud (*cloud, angularResolution, maxAngleWidth, maxAngleHeight,
                                  sensorPose, coordinate_frame, noiseLevel, minRange, borderSize);

  // --------------------------------------------
  // -----Open 3D viewer and add point cloud-----
  // --------------------------------------------
  pcl::visualization::PCLVisualizer viewer ("3D Viewer");
  viewer.setBackgroundColor (1, 1, 1);
  pcl::visualization::PointCloudColorHandlerCustom<pcl::PointWithRange> range_image_color_handler (range_image_ptr, 0, 0, 0);
  viewer.addPointCloud (range_image_ptr, range_image_color_handler, "range image");
  viewer.setPointCloudRenderingProperties (pcl::visualization::PCL_VISUALIZER_POINT_SIZE, 1, "range image");
  //viewer.addCoordinateSystem (1.0f);
  //PointCloudColorHandlerCustom<PointType> point_cloud_color_handler (point_cloud_ptr, 150, 150, 150);
  //viewer.addPointCloud (point_cloud_ptr, point_cloud_color_handler, "original point cloud");
  viewer.initCameraParameters ();
  setViewerPose(viewer, range_image.getTransformationToWorldSystem ());
  
  // --------------------------
  // -----Show range image-----
  // --------------------------
  pcl::visualization::RangeImageVisualizer range_image_widget ("Range image");
  range_image_widget.showRangeImage (range_image);
  
  //--------------------
  // -----Main loop-----
  //--------------------
  while (!viewer.wasStopped ())
  {
    range_image_widget.spinOnce ();
    viewer.spinOnce ();
    pcl_sleep (0.01);
    }

    //convert to flat image/ png of range? hmm...
    //unsigned char* getImageData (int& width, int& height) const 
    //range Image should have height and width, but may not: pc->range problem...
    //std::cout<<"DEBUG: range image height and width: "<<range_image.height<<" , "<<range_image.width<<std::endl;
    //open the file
    ofstream file1;
    pcl::PointCloud<pcl::PointXYZRGBA>::iterator b1;
    file1.open(("../pics/"+filename+"Cloud").c_str());
    if(file1.is_open()){
        for (b1 = (*cloud).points.begin(); b1 < (*cloud).points.end(); b1++)
        {
          file1<<(*b1)<<"\n";
        }

        file1.close();
    }

    ofstream file;
    int crap;
    file.open(("../pics/"+filename).c_str());
    if(file.is_open())
    {
        //write range points to it.
        file<<"Height "<<range_image.height<<" Width "<<range_image.width<<"\n";
        for (int image_y=0; image_y<int(range_image.height); ++image_y) 
        { 
            for (int image_x=0; image_x<int(range_image.width); ++image_x) 
            { 
                //point with range should be x,y,z + xi, yi + range...no color?
                pcl::PointWithRange& point = range_image.getPoint(image_x, image_y);
                if (pcl_isfinite(point.x) && pcl_isfinite(point.y) && pcl_isfinite(point.x))
                { 
                    //std::cout<<point<<std::endl;//point cout function?
                    //std::cin>>crap;
                    //check if range points are findable in point cloud...
                    file<<point.x<<' '<<point.y<<' '<<point.z<<", "<<point.range<<" "<<image_x<<' '<<image_y<<'\n';
                    //if we want color, we need point_cloud data...
                    //add to png? or save points then write separte file for making png....
                    //if we save we can use python to load. Might be a lot easier then libpng c++ stuff...
                }
            }
            file<<"End Row \n"; 
        } 
        file.close();
    }

    bool 	isInImage (int x, int y) const
 	Check if a point is inside of the image. 
 	const PointWithRange & 	getPoint (int image_x, int image_y) const
 	Return the 3D point with range at the given image position. 
*/

