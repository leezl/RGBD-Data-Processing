/*
This began as the pcl tutorial on the use of OpenNI, but I expanded it to perform some of the other tutorial processing on the point clouds.

There are some issues, probably still some Seg Faults lying in wait.

Right now the callback is the only way to get a cloud.

In order to get the clouds you need to restart the cloud_viewer. I have not found a way to restart this without deleting it and making a new one. Also if you close the display window it will need to be restarted.

Right now grabCloud just takes a copy of the last cloud produced by the callback, and does not grab whatever is currently being seen (which is why you must display the cloud before grabbing one.)

I do not have the point cloud saving set up. I didn't need it.

There is a default call back function that does not perform any checks or processing.

The other one performs everything. It was not set up to be fast.

Ideally I would be keeping pointer of everything and not be passing clouds ever. This would certainly speed things up.

*/

#include <pcl/io/openni_grabber.h>
#include <pcl/visualization/cloud_viewer.h>
#include <pcl/point_types.h>
#include <pcl/filters/passthrough.h>
#include <pcl/sample_consensus/method_types.h>
#include <pcl/sample_consensus/model_types.h>
#include <pcl/segmentation/sac_segmentation.h>
#include <pcl/ModelCoefficients.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/filters/extract_indices.h>
#include "pcl/surface/convex_hull.h"
#include "pcl/segmentation/extract_polygonal_prism_data.h"
#include "pcl/filters/project_inliers.h"

 class SimpleOpenNIViewer
 {
   public:
     //Most of these are to keep track of processing
     bool displaying, filtering, firstFilter;
     float near, far, left, right, up, down, fVal;
     std::string axis;
     //this is needed to see anything
     pcl::visualization::CloudViewer * viewer;
     pcl::Grabber* interface;
     pcl::PointCloud<pcl::PointXYZRGBA>::Ptr inCloud;
     //These are only needed for advanced planar segmentation
     pcl::PointCloud<pcl::PointXYZRGBA>::Ptr table_hull;
     pcl::ExtractIndices<pcl::PointXYZRGBA> extract;
     pcl::ExtractPolygonalPrismData<pcl::PointXYZRGBA> prism_;
     pcl::ModelCoefficients::Ptr coefficients;
     pcl::PointIndices::Ptr inliers;
     //friend class pcl::PassThrough<pcl::PointXYZRGBA>;

    //constructor that initializes everything
     SimpleOpenNIViewer () : displaying(false), filtering(false), firstFilter(true), fVal(-1.0), near(0.0), far(0.0), left(0.0), right(0.0), up(0.0), down(0.0), inCloud(new pcl::PointCloud<pcl::PointXYZRGBA>), table_hull(new pcl::PointCloud<pcl::PointXYZRGBA>), inliers (new pcl::PointIndices), coefficients (new pcl::ModelCoefficients) {}


    //This is the default callback that only displays the cloud
     void default_cloud_cb_ (const pcl::PointCloud<pcl::PointXYZRGBA>::ConstPtr &cloud)
     {

       if (!viewer->wasStopped())
         viewer->showCloud (cloud);
     }

////////////////////Callback Begin/////////////////////////
     void cloud_cb_ (const pcl::PointCloud<pcl::PointXYZRGBA>::ConstPtr &cloud)
     {
        //std::cout<<"Depth Filtering..."<<std::endl;
	    pcl::PointCloud<pcl::PointXYZRGBA>::Ptr procCloud (new pcl::PointCloud<pcl::PointXYZRGBA>);
        pcl::PointCloud<pcl::PointXYZRGBA>::Ptr tempCloud (new pcl::PointCloud<pcl::PointXYZRGBA>);
	    //copy may be time consuming
        pcl::copyPointCloud<pcl::PointXYZRGBA,pcl::PointXYZRGBA>(*cloud, *procCloud);

        //create filter
        pcl::PassThrough<pcl::PointXYZRGBA> pass(false);

        //check filter planes
        if(filtering)
        {
            if(firstFilter)//Planar Segmentation calculate once. If motion, this fails
            {
                //std::cout<<"filtering"<<std::endl;
                //remove point from filter function
                //Find Table etc:
                // Create the segmentation object
                pcl::SACSegmentation<pcl::PointXYZRGBA> seg;
                pcl::PointCloud<pcl::PointXYZRGBA>::Ptr table(new pcl::PointCloud<pcl::PointXYZRGBA>);
                // Optional
                seg.setOptimizeCoefficients (true);
                // Mandatory
                seg.setModelType (pcl::SACMODEL_PLANE);
                seg.setMethodType (pcl::SAC_RANSAC);
                seg.setMaxIterations (1000);//
                seg.setProbability (0.99);//
                seg.setDistanceThreshold (fVal);

                seg.setInputCloud ((procCloud->makeShared ()));//procCloud //filter twice?
                seg.segment (*inliers, *coefficients);

                /*pcl::ProjectInliers<pcl::PointXYZRGBA> proj_;//
                proj_.setModelType(pcl::SACMODEL_PLANE);//
                proj_.setInputCloud (procCloud);//
                proj_.setIndices (inliers);//
                proj_.setModelCoefficients (coefficients);//
                proj_.filter(*table);//

                pcl::ConvexHull<pcl::PointXYZRGBA> hull_;//
                hull_.setInputCloud (table);
                hull_.reconstruct (*table_hull);*/

                firstFilter=false;
            }

            //Remove Table:
            //use proc Cloud?
            //std::cout<<"extracting"<<std::endl;
            // Create the filtering object//
            /*pcl::PointIndices cloud_object_indices;
            prism_.setInputCloud (procCloud);
            prism_.setInputPlanarHull (table_hull);
            prism_.segment (cloud_object_indices);*/

            // Extract the inliers
            extract.setKeepOrganized(true);//this keeps shape
            extract.setUserFilterValue(std::numeric_limits<float>::quiet_NaN());//this replaces points...somehow
            extract.setInputCloud (procCloud);
            //extract.setIndices (boost::make_shared<const pcl::PointIndices> (cloud_object_indices));
            extract.setIndices (inliers);
            extract.setNegative (true);
            extract.filter (*tempCloud);

            //copy may be time consuming, maybe fix with bool check
            pcl::copyPointCloud<pcl::PointXYZRGBA,pcl::PointXYZRGBA>(*tempCloud, *procCloud);
        }

        //check filter depth
        if(near <far)
        {
            //std::cout<<"near/far"<<std::endl;
            //std::vector<int> indices;
            pass.setKeepOrganized(true);
            pass.setUserFilterValue(std::numeric_limits<float>::quiet_NaN());
            //set input cloud
            pass.setInputCloud(procCloud);
            //set filter direction: far to near, z-axis
            pass.setFilterFieldName("z");
            //set filter distance, needs playing
            pass.setFilterLimits(near, far);
            //pass.setFilterLimitsNegative (true);
            pass.filter(*tempCloud);
            //pass.applyFilter(indices);//returns filtered points, change these, and add back in.

            //copy back into procCloud
            pcl::copyPointCloud<pcl::PointXYZRGBA,pcl::PointXYZRGBA>(*tempCloud, *procCloud);
        }

        //check filter height
        if(down<up)
        {
            //std::cout<<"down/up"<<std::endl;
            //std::vector<int> indices;
            pass.setKeepOrganized(true);
            pass.setUserFilterValue(std::numeric_limits<float>::quiet_NaN());
            //set input cloud
            pass.setInputCloud (procCloud);
            //set filter direction: far to near, z-axis
            pass.setFilterFieldName ("y");
            //set filter distance, needs playing
            pass.setFilterLimits (down, up);
            //pass.setFilterLimitsNegative (true);
            pass.filter (*tempCloud);
            //pass.applyFilter(indices);
            
            //copy back into procCloud
            pcl::copyPointCloud<pcl::PointXYZRGBA,pcl::PointXYZRGBA>(*tempCloud, *procCloud);
        }

        //check filter width
        if(left<right)
        {
            //std::cout<<"laft/right"<<std::endl;
            pass.setKeepOrganized(true);
            pass.setUserFilterValue(std::numeric_limits<float>::quiet_NaN());
            //set input cloud
            pass.setInputCloud (procCloud);
            //set filter direction: far to near, z-axis
            pass.setFilterFieldName ("x");
            //set filter distance, needs playing
            pass.setFilterLimits (left, right);
            //pass.setFilterLimitsNegative (true);
            pass.filter (*tempCloud);
            
            //copy back into procCloud
            pcl::copyPointCloud<pcl::PointXYZRGBA,pcl::PointXYZRGBA>(*tempCloud, *procCloud);
        }
        
        //Make sure everything is ready for display
        if(near>=far && down>=up && left>=right && !filtering)
        {
            //std::cout<<"copying normal"<<std::endl;
            pcl::copyPointCloud<pcl::PointXYZRGBA,pcl::PointXYZRGBA>(*cloud, *inCloud);
        }else{
            pcl::copyPointCloud<pcl::PointXYZRGBA,pcl::PointXYZRGBA>(*tempCloud, *inCloud);
        }

        //print (check cloud in inCloud)

        //FINALLY the part that displays
       if (!viewer->wasStopped() && !inCloud->empty())
        {
         //std::cout<<"Displaying"<<std::endl;
         viewer->showCloud (inCloud);
        }
     }
////////////////////Callback End///////////////////////////

     void display ()
     {
       //if(displaying==false)
       //{//start displaying
           
           //if(viewer->wasStopped())//this does not work. wasStopped is reset somehow
           // {
           //     std::cout<<"Restarting Viewer..."<<std::endl;
                //restart viewer?
           //     delete viewer;
                viewer = new pcl::visualization::CloudViewer("PCL Openni Viewer");
            //}

	       //displaying=true;//This failed due to openni weirdness

           interface = new pcl::OpenNIGrabber();

           boost::function<void (const pcl::PointCloud<pcl::PointXYZRGBA>::ConstPtr&)> f =
             boost::bind (&SimpleOpenNIViewer::cloud_cb_, this, _1);

           interface->registerCallback (f);

           interface->start ();

           while (!viewer->wasStopped())
           {
             boost::this_thread::sleep (boost::posix_time::seconds (1));
           }

           interface->stop ();
           
           //The following has to be in this order, otherwise the callback runs on NULL pointers...
           delete interface;
           delete viewer;//seg faults?
        //}
        //else
        //{//stop displaying
            //delete viewer;
	    //    displaying =false;
        //}
     }

    void showCloud(pcl::PointCloud<pcl::PointXYZRGBA>::Ptr cloud)
    {
        viewer = new pcl::visualization::CloudViewer("PCL Openni Viewer");
        
        viewer->showCloud(cloud);

        delete interface;
        delete viewer;
    }

    pcl::PointCloud<pcl::PointXYZRGBA>::Ptr getCloud()
    {
        if(inCloud->empty()){std::cout<<"Warning: Empty Cloud"<<std::endl;}
        return inCloud;
    }

    void setDepthFilter(float close, float distant)
    {
        near = close;
        far = distant;
    }

    void setWidthFilter(float l, float r)
    {
        left = l;
        right=r;
    }

    void setHeightFilter(float d, float u)
    {
        down=d;
        up=u;
    }

    void setTableFilter(float val)
    {
        fVal=val;
        filtering=true;
        firstFilter=true;
    }

 };
/*
 int main ()
 {
   SimpleOpenNIViewer v;
   v.display ();
   return 0;
 }
*/
