"""
Prototype script to get images from Basler GIGe cameras

This is a prototype script and as such has several this still need to done, see 
below.

Prerequisites
-------------

Pylon software - PyPylon is just python bindings to the C++ pylon software, the 
pylon software should be reinstalled.

:TODO:
1[SIMPLE] Move config objects to files that can be read -[UPDATE 27/09/2018] Config 
objects are less useful current use case is separate initialisation, exposure time 
and image acquisition steps.

2[COMPLEX] Determine the best grab strategy (see samples/grabstrategies.py , while 
developing my strategy is to do the least configuration possible.

3 [SIMPLE] Throw pretty exception when file already exists, need to manually check 
imsave clobbers. [UPDATE] According to SW this is acceptable behaviour. Calling code 
does not have a default save location.

:DONE:
4 [Complex] Add support for changing the exposure time.

:History:
31/08/2018: Creation AOB
03/09/2018: Fixed countOfImagesToGrab variable not existing. Version delivered as 
            prototype 0.1
20/09/2018: 0.2.0 Updated to include exposure time parameter
27/09/2018: 0.3.0 Refactoring to an OOP design
01/10/2018: 0.3.1 Fixed Error and added support to find a camera.
03/10/2018: 0.3.2 Fixed indent issues and updated documentation.

27/10/2020: Added saveBurst method. (SMB)

"""
from __future__ import division, print_function

import logging
import numpy as np
import time

__version__ = "0.3.2"


try:
    from pypylon import pylon
    from pypylon import genicam
except ImportError:
    logging.warning(
        ">>>>>>>>>>> Warning: Import of Basler pylon software failed - probably not installed."
    )
    pylon = None
    genicam = None

try:
    from scipy.misc import imsave
except ImportError:
    logging.warning(
        ">>>>>>>>>>> Warning: Import of scipy.misc.imsave failed - probably dependency mismatch."
    )


__author__ = "Alan O'Brien"

DEVICE_CLASS = "DeviceClass"
IP_ADDRESS = "IpAddress"
BASLER_DEVICE_CLASS = "BaslerGigE"

# Currently used camera in the lab.
TEST_CAMERA = {DEVICE_CLASS: BASLER_DEVICE_CLASS, IP_ADDRESS: "169.254.187.121"}
# For history the EXPOSURE_TIME is 499975

# Dev device on desk.
DEV_CAMERA = {DEVICE_CLASS: BASLER_DEVICE_CLASS, IP_ADDRESS: "169.254.244.184"}


class GigECamera(object):
    """
    
    Prototype GIGeCamera interface.

    Simple Object design for the Basler GIGe cameras being used for the MOONs 
    verification rig. The camera will open upon initialisation but needs to closed 
    manually.

    """

    def __init__(self, device_config):
        """
        
        Create the Basler GIGe camera device.

        Parameters
        ----------
        device_config : dictionary

            dictionary containing the device configuration, currently this is the IP 
            address (IpAddress) and the pypylon class device (DeviceClass). The only 
            useful value for DeviceClass is currently "BaslerGigE". If None is 
            given, will use the camera finding tool and connect to the first one 
            found.

        """
        logger = logging.getLogger(__name__)
        logger.debug("Starting Setup")
        if device_config is None:
            # Create an instant camera object with the camera device found first.
            logger.debug("No device config specified, using first camera found")
            self.camera = pylon.InstantCamera(
                pylon.TlFactory.GetInstance().CreateFirstDevice()
            )
        else:
            # Create a camera object for the specific device.
            factory = pylon.TlFactory.GetInstance()
            di = pylon.DeviceInfo()
            di.SetDeviceClass(device_config[DEVICE_CLASS])
            di.SetPropertyValue(IP_ADDRESS, device_config[IP_ADDRESS])
            device = factory.CreateDevice(di)
            self.camera = pylon.InstantCamera(device)

        logger.debug("Gained access to Camera")

        # FROM HERE USES SAMPLES/GRAB.PY

        # Print the model name of the camera.
        logger.debug("Using device %s" % self.camera.GetDeviceInfo().GetModelName())

        # Camera needs to be open to change the exposure time, normal 
        # camera.StartGrabbingMax will open a camera but this is an explicit call
        self.camera.Open()


    def SetExposureTime(self, exposure_time):
        """
        
        Set the exposure time of the camera.

        Parameters
        ----------
        exposure_time : int
            sets the raw exposure time in ms.
            
        """
        logger = logging.getLogger(__name__)
        # convert exposure time from milliseconds to microseconds where the
        # value is an integral multiple of 35 microseconds
        EXPOSURE_STEP_US = 35
        US_PER_MS = 1000
        exposure_time_us = EXPOSURE_STEP_US * int(
            round(US_PER_MS * exposure_time / float(EXPOSURE_STEP_US))
        )
        logger.debug("Setting exposure time to %f us" % exposure_time_us)
        if genicam.IsWritable(self.camera.ExposureTimeRaw):
            self.camera.ExposureTimeRaw.SetValue(exposure_time_us)
        else:
            logger.warning(
                "Exposure Time is not settable, continuing with current exposure time."
            )


    def saveImage(self, filename):
        """
        
        Function to save a single image from a camera device and save it to a location.
        Overwrites any existing file at filename.
        
        Parameters
        ----------
        filename : str
            Path to location where the image will be saved.

        """
        logger = logging.getLogger(__name__)
        # The parameter MaxNumBuffer can be used to control the count of buffers
        # allocated for grabbing. The default value of this parameter is 10.
        # Only one image is grabbed, so the buffer size can be 1.
        self.camera.MaxNumBuffer = 1

        # Only grab a single image.
        countOfImagesToGrab = 1

        # Start the grabbing of c_countOfImagesToGrab images.
        # The camera device is parameterized with a default configuration which
        # sets up free-running continuous acquisition.
        self.camera.StartGrabbingMax(countOfImagesToGrab)

        # Camera.StopGrabbing() is called automatically by the RetrieveResult() method
        # when c_countOfImagesToGrab images have been retrieved.
        while self.camera.IsGrabbing():
            # Wait for an image and then retrieve it. A timeout of 5000 ms is used.
            grabResult = self.camera.RetrieveResult(
                5000, pylon.TimeoutHandling_ThrowException
            )

            # Image grabbed successfully?
            if grabResult.GrabSucceeded():
                # Access the image data.
                img = grabResult.Array
                imsave(filename, np.asarray(img))
                logger.debug("File saved as : {}".format(filename))
            else:
                logger.error(
                    "Error: %r %s" % (grabResult.ErrorCode, grabResult.ErrorDescription)
                )
        grabResult.Release()


    def saveBurst(self, filestub, number_of_images=1, sleep_time_ms=0, timeout=2000):
        """
        
        Function to save a burst of images from a camera device and saves them to a location.
        Overwrites any existing file at filename.
        
        Option 1 - StartGrabbingMax mode.
        
        Parameters
        ----------
        filestub : str
            Path and filename stub to location where the images will be saved.
            The files will have "_<N>.bmp" appended to their name.

        """
        logger = logging.getLogger(__name__)
        # The parameter MaxNumBuffer can be used to control the count of buffers
        # allocated for grabbing. The default value of this parameter is 10.
        self.camera.MaxNumBuffer = 15

        # Only grab a single image.
        countOfImagesToGrab = number_of_images

        # Start the grabbing of c_countOfImagesToGrab images.
        # The camera device is parameterized with a default configuration which
        # sets up free-running continuous acquisition.
        self.camera.StartGrabbingMax(countOfImagesToGrab)

        # Camera.StopGrabbing() is called automatically by the RetrieveResult() method
        # when c_countOfImagesToGrab images have been retrieved.
        count = 0
        while self.camera.IsGrabbing():
            # Wait for an image and then retrieve it. A timeout of 5000 ms is used.
            grabResult = self.camera.RetrieveResult(
                timeout, pylon.TimeoutHandling_ThrowException
            )

            # Image grabbed successfully?
            if grabResult.GrabSucceeded():
                count += 1
                #print("Grab", count)
                filename = "%s_%d.bmp" % (filestub, count)
                # Access the image data.
                img = grabResult.Array
                imsave(filename, np.asarray(img))
                logger.debug("File {} saved as : {}".format(count, filename))
            else:
                logger.error(
                    "Error: %r %s" % (grabResult.ErrorCode, grabResult.ErrorDescription)
                )
            # Wait for next frame, if required.
            if sleep_time_ms > 0.0:
                time.sleep( sleep_time_ms / 1000.0 )
        grabResult.Release()


    def startGrabbing(self, maxbuffer=15, frametime=200):
        """
        
        Function to collect a burst of images from a camera deviceusing the
        GrabStrategy_OneByOne  mode.
        
        Parameters
        ----------
        filestub : str
            Path and filename stub to location where the images will be saved.
            The files will have "_<N>.bmp" appended to their name.

        """
        logger = logging.getLogger(__name__)
        
        # The parameter MaxNumBuffer can be used to control the count of buffers
        # allocated for grabbing. The default value of this parameter is 10.
        self.camera.MaxNumBuffer = maxbuffer
        
        # The GrabStrategy_OneByOne strategy is used. The images are processed
        # in the order of their arrival.
        self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne)
        print("Grabbing started...")
        
        # In the background, the grab engine thread retrieves the
        # image data and queues the buffers into the internal output queue.
                
    def triggerGrabbing(self, frametime, nframes=1):
        """
        
        Trigger the camera to grab a frame and wait up to the given frame time
        
        """
        # Issue software triggers. For each call, wait up to 200 ms until the camera is ready for triggering the next image.
        print("Triggering grabbing for %d frames..." % nframes )
        for i in range(nframes):
            #print("Frame %d..." % i )
            if self.camera.WaitForFrameTriggerReady(frametime, pylon.TimeoutHandling_ThrowException):
                self.camera.ExecuteSoftwareTrigger()

    def finishGrabbing(self, filestub, maxcount, timeout=0):
        """
        
        Save all the frames to files.
        
        """
        logger = logging.getLogger(__name__)
        # For demonstration purposes, wait for the last image to appear in the output queue.
        #time.sleep(0.2)

        # All triggered images are still waiting in the output queue
        # and are now retrieved.
        # The grabbing continues in the background, e.g. when using hardware trigger mode,
        # as long as the grab engine does not run out of buffers.
        count = 0
        buffersInQueue = 0
        grabSucceeded = True
        print("Retrieving results..." )
        while grabSucceeded and count < maxcount:
            #print("Retrieving next frame...")
            grabResult = self.camera.RetrieveResult(timeout, pylon.TimeoutHandling_Return)
            grabSucceeded = grabResult.GrabSucceeded()
            if grabSucceeded:
                count += 1
                #print("Got frame %d" % count)
                filename = "%s_%d.bmp" % (filestub, count)
                # Access the image data.
                img = grabResult.Array
                imsave(filename, np.asarray(img))
                logger.debug("File {} saved as : {}".format(count, filename))
            else:
                logger.error(
                    "Error: %r %s" % (grabResult.ErrorCode, grabResult.ErrorDescription)
                    )
            buffersInQueue += 1

        print("Retrieved ", buffersInQueue, " grab results from output queue.")

        # Stop the grabbing.
        self.camera.StopGrabbing()


    def close(self):
        """
        
        If open, close access to camera.
        
        """
        logger = logging.getLogger(__name__)
        if self.camera.IsOpen():
            self.camera.Close()
        else:
            logger.error("Camera is already closed.")


    def __del__(self):
        # Destructor
        self.close()
