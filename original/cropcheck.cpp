/*
Test the crop values of lab files vs rgbd files

  //load crop values
  std::ifstream ifs;

  ifs.open (filename+"_crop.txt", std::ifstream::in);
  int cropval;
  ifs>>cropval;
  while (ifs.good()) {
    std::cout << cropval;
    ifs>>cropval;;
  }
  ifs.close();
*/

#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <string>

#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/highgui/highgui_c.h>
#include <opencv2/imgproc/imgproc.hpp>


struct crop {
    int minx;
    int miny;
    int maxx;
    int maxy;
};

crop loadCrop(std::string filename) {
    //load crop values
    std::ifstream ifs;
    crop temp;
    char ok;
    std::string argh = "";
    ifs.open ((filename+"_crop.txt").c_str(), std::ifstream::in);
    int cropval[4] = {-1};
    int i=0;
    //ifs>>cropval[i];
    std::getline(ifs,argh, ' ');
    cropval[i] = std::stoi(argh);
    while (ifs.good() && i<4) {
        std::cout << cropval[i]<<',';
        i++;
        //ifs>>ok;//space skipper
        //ifs>>cropval[i];
        std::getline(ifs,argh, ' ');
        cropval[i] = std::stoi(argh);
    }
    ifs.close();
    std::cout<<"\n";

    for( i=0; i<4; i++) {
        std::cout<<cropval[i]<<',';
    }
    std::cout<<std::endl;

    temp.minx = cropval[0];
    temp.miny = cropval[1];
    temp.maxx = cropval[2];
    temp.maxy = cropval[3];
    std::cout<<"imaprompt-> ";
    std::cin>>ok;

    return temp;
}

cv::Mat loadImage(std::string filename) {
    //load color
    cv::Mat cv_img = cv::imread((filename+".png"), CV_LOAD_IMAGE_COLOR);
    if (!cv_img.data) {
      std::cout<< "Could not open or find file " << filename+".png";
      exit (EXIT_FAILURE);
    }
    return cv_img;
}

void displayImageWithCrop(cv::Mat image, crop cropVal) {
    if (!image.data) {
        std::cout<<"NO IMAGE "<<std::endl;
        exit(EXIT_FAILURE);
    }
    cv::Mat tempImage = image.clone();
    std::cout<<tempImage.rows<<','<<tempImage.cols<<','<<std::endl;
    if (cropVal.maxx > image.cols) {
        std::cout<<"x values wrong "<<std::endl;
        std::cout<<cropVal.maxx<<std::endl;
        exit(EXIT_FAILURE);
    }
    if (cropVal.maxy > image.rows) {
        std::cout<<"y values wrong "<<std::endl;
        std::cout<<cropVal.maxy<<std::endl;
        exit(EXIT_FAILURE);
    }
    //change values along the crop lines to be bright red...
    int mytype = tempImage.type();
    for(int i=cropVal.minx; i<cropVal.maxx; i++) {
        tempImage.at<cv::Vec3b>(cropVal.miny, i)[0] = 255;
        tempImage.at<cv::Vec3b>(cropVal.maxy, i)[0] = 255;
        tempImage.at<cv::Vec3b>(cropVal.miny, i)[1] = 0;
        tempImage.at<cv::Vec3b>(cropVal.maxy, i)[1] = 0;
        tempImage.at<cv::Vec3b>(cropVal.miny, i)[2] = 0;
        tempImage.at<cv::Vec3b>(cropVal.maxy, i)[2] = 0;
    }
    for (int j=cropVal.miny; j<cropVal.maxy; j++) {
        //change value to red
        tempImage.at<cv::Vec3b>(j, cropVal.minx)[0] = 255;
        tempImage.at<cv::Vec3b>(j, cropVal.maxx)[0] = 255;
        tempImage.at<cv::Vec3b>(j, cropVal.minx)[1] = 0;
        tempImage.at<cv::Vec3b>(j, cropVal.maxx)[1] = 0;
        tempImage.at<cv::Vec3b>(j, cropVal.minx)[2] = 0;
        tempImage.at<cv::Vec3b>(j, cropVal.maxx)[2] = 0;
    }
    //display the new image
    cv::imshow("crop", tempImage);
    cv::waitKey(0);
}

int main() {
    //take two filenames
    std::string labfile = "lab/temp/aibo_1/aibo_1384552253.8";
    std::string rgbdfile = "tared/temp/rgbd-dataset/flashlight/flashlight_1/flashlight_1_1_1";

    //open first image and crop
    cv::Mat labimg = loadImage(labfile);
    crop labcrop = loadCrop(labfile);

    //open second image and crop
    cv::Mat rgbdimg = loadImage(rgbdfile);
    crop rgbdcrop = loadCrop(rgbdfile);

    //display image1 and crop
    displayImageWithCrop(rgbdimg, rgbdcrop);

    //display image2 and crop
    displayImageWithCrop(labimg, labcrop);

    //if these don't seem right, we need to update, probably the lab crop values. For consistancy.


    return 0;
}