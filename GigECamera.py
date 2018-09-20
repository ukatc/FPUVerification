"""
Prototype script to get images from Basler GIGe cameras

This is a prototype script and as such has several this still need to done, see below.

:TODO:
1[SIMPLE] Move config objects to files that can be read
2[COMPLEX] Determine the best grab strategy (see samples/grabstrategies.py , while developing my strategy is to do the least configuration possible.
3 [SIMPLE] Throw pretty exception when file already exists, need to manually check imsave clobbers. [UPDATE] According to SW this is acceptable behaviour. Calling code does not have a default save location.

:DONE:
4 [Complex] Add support for changing the exposure time.

:History:
31/08/2018: Creation AOB
03/09/2018: Fixed countOfImagesToGrab variable not existing. Version delivered as prototype 0.1
20/09/2018: 0.2.0 Updated to include exposure time parameter
"""
from pypylon import pylon
from pypylon import genicam

import sys

import numpy as np
from scipy.misc import imsave

__version__ = 0.2.0
__author__ = "Alan O'Brien"

DEVICE_CLASS = "DeviceClass"
IP_ADDRESS = "IpAddress"
BASLER_DEVICE_CLASS = "BaslerGigE"

TEST_CAMERA = {DEVICE_CLASS :BASLER_DEVICE_CLASS,
                IP_ADDRESS :"169.254.187.121",
                EXPOSURE_TIME: 499975}


def saveImageFromCamera(device_config, filename):
    """Function to save an image from a camera device and save it to a location.
    
    Connect to a Basler GIGe camera via the pypylon software suite.
    
    Parameters
    ----------
    device_config : dictionary
        dictionary containing the device configuration, currently this is the IP address (IpAddress) and the pypylon class device (DeviceClass). The only useful value for DeviceClass is currently "BaslerGigE"
    filename : str
        Path to location where the image will be saved.
        
    """
    print("Starting Setup")
    factory = pylon.TlFactory.GetInstance()
    di = pylon.DeviceInfo()
    di.SetDeviceClass(device_config[DEVICE_CLASS])
    di.SetPropertyValue(IP_ADDRESS,device_config[IP_ADDRESS])
    device = factory.CreateDevice(di)
    camera = pylon.InstantCamera(device)
    
    print("Gained access to Camera")
    
    #FROM HERE USES SAMPLES/GRAB.PY 
    
    # Print the model name of the camera.
    print("Using device ", camera.GetDeviceInfo().GetModelName())
    
    
    # Camera needs to be open to change the exposure time, normal camera.StartGrabbingMax will open a camera but this is an explicit call
    camera.Open()
    
    if genicam.isWritable(camera.ExposureTimeRaw):
        camera.ExposureTimeRaw.SetValue(device_config[EXPOSURE_TIME])
    else:
        print("Exposure Time is not settable, continuing with current exposure time.")
    # The parameter MaxNumBuffer can be used to control the count of buffers
    # allocated for grabbing. The default value of this parameter is 10.
    camera.MaxNumBuffer = 1
    
    #
    countOfImagesToGrab = 1

    # Start the grabbing of c_countOfImagesToGrab images.
    # The camera device is parameterized with a default configuration which
    # sets up free-running continuous acquisition.
    camera.StartGrabbingMax(countOfImagesToGrab)

    # Camera.StopGrabbing() is called automatically by the RetrieveResult() method
    # when c_countOfImagesToGrab images have been retrieved.
    while camera.IsGrabbing():
        # Wait for an image and then retrieve it. A timeout of 5000 ms is used.
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        # Image grabbed successfully?
        if grabResult.GrabSucceeded():
            # Access the image data.
            img = grabResult.Array
            imsave(filename,np.asarray(img))
            print("Filesaved as : {}".format(filename))
	else:
            print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
        grabResult.Release()
    
