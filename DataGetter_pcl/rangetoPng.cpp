
void pcl::io::saveRangeImagePlanarFilePNG (const std::string &file_name, const pcl::RangeImagePlanar& range_image) 
{ 
  vtkSmartPointer<vtkImageData> image = vtkSmartPointer<vtkImageData>::New(); 
  image->SetDimensions(range_image.width, range_image.height, 1); 
  image->SetNumberOfScalarComponents(1); 
  image->SetScalarTypeToFloat(); 
  image->AllocateScalars(); 

  int* dims = image->GetDimensions(); 

  std::cout << "Dims: " << " x: " << dims[0] << " y: " << dims[1] << " z: " << dims[2] << std::endl; 

  for (int y = 0; y < dims[1]; y++) 
    { 
    for (int x = 0; x < dims[0]; x++) 
      { 
      float* pixel = static_cast<float*>(image->GetScalarPointer(x,y,0)); 
      pixel[0] = range_image(y,x).range; 
      } 
    } 

  // Compute the scaling 
  float oldRange = image->GetScalarRange()[1] - image->GetScalarRange()[0]; 
  float newRange = 255; // We want the output [0,255] 

  vtkSmartPointer<vtkImageShiftScale> shiftScaleFilter = vtkSmartPointer<vtkImageShiftScale>::New(); 
  shiftScaleFilter->SetOutputScalarTypeToUnsignedChar(); 
  shiftScaleFilter->SetInputConnection(image->GetProducerPort()); 
  shiftScaleFilter->SetShift(-1.0f * image->GetScalarRange()[0]); // brings the lower bound to 0 
  shiftScaleFilter->SetScale(newRange/oldRange); 
  shiftScaleFilter->Update(); 

  vtkSmartPointer<vtkPNGWriter> writer = vtkSmartPointer<vtkPNGWriter>::New(); 
  writer->SetFileName(file_name.c_str()); 
  writer->SetInputConnection(shiftScaleFilter->GetOutputPort()); 
  writer->Write(); 
} 
