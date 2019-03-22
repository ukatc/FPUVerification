"""
Prototype script to get images from Basler GIGe cameras

This is a prototype script and as such has several this still need to done, see below.

Prerequisites
-------------
Pylon software - PyPylon is just python bindings to the C++ pylon software, the pylon software should be reinstalled.

:TODO:
1[SIMPLE] Move config objects to files that can be read -[UPDATE 27/09/2018] Config objects are less useful current use case is separate initialisation, exposure time and image acquisition steps.
2[COMPLEX] Determine the best grab strategy (see samples/grabstrategies.py , while developing my strategy is to do the least configuration possible.
3 [SIMPLE] Throw pretty exception when file already exists, need to manually check imsave clobbers. [UPDATE] According to SW this is acceptable behaviour. Calling code does not have a default save location.

:DONE:
4 [Complex] Add support for changing the exposure time.

:History:
31/08/2018: Creation AOB
03/09/2018: Fixed countOfImagesToGrab variable not existing. Version delivered as prototype 0.1
20/09/2018: 0.2.0 Updated to include exposure time parameter
27/09/2018: 0.3.0 Refactoring to an OOP design
01/10/2018: 0.3.1 Fixed Error and added support to find a camera.
03/10/2018: 0.3.2 Fixed indent issues and updated documentation.
"""
from __future__ import print_function, division

__version__ = "0.3.2"

import sys

import numpy as np

try:
    from pypylon import pylon
    from pypylon import genicam
except ImportError:
    print(
        ">>>>>>>>>>> Warning: Import of Basler pylon software failed - probably not installed."
    )
    pylon = None
    genicam = None

try:
    from scipy.misc import imsave
except ImportError:
    print(
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
    """ Prototype GIGeCamera interface.

    Simple Object design for the Basler GIGe cameras being used for the MOONs verification rig. The camera will open upon initialisation but needs to closed manually.

    """

    def __init__(self, device_config):
        """ Create the Basler GIGe camera device.

        Parameters
        ----------
        device_config : dictionary
            dictionary containing the device configuration, currently this is the IP address (IpAddress) and the pypylon class device (DeviceClass). The only useful value for DeviceClass is currently "BaslerGigE". If None is given, will use the camera finding tool and connect to the first one found.
        """
        print("Starting Setup")
        if device_config is None:
            print("No device config specified, using first camera found")
            self.camera = pylon.InstantCamera(
                pylon.TlFactory.GetInstance().CreateFirstDevice()
            )
        else:
            factory = pylon.TlFactory.GetInstance()
            di = pylon.DeviceInfo()
            di.SetDeviceClass(device_config[DEVICE_CLASS])
            di.SetPropertyValue(IP_ADDRESS, device_config[IP_ADDRESS])
            device = factory.CreateDevice(di)
            self.camera = pylon.InstantCamera(device)

        print("Gained access to Camera")

        # FROM HERE USES SAMPLES/GRAB.PY

        # Print the model name of the camera.
        print("Using device ", self.camera.GetDeviceInfo().GetModelName())

        # Camera needs to be open to change the exposure time, normal camera.StartGrabbingMax will open a camera but this is an explicit call
        self.camera.Open()

    def SetExposureTime(self, exposure_time):
        """Set the exposure time of the camera.

        Parameters
        ----------
        exposure_time : int
            sets the raw exposure time in ms.
        """

        if genicam.isWritable(self.camera.ExposureTimeRaw):
            self.camera.ExposureTimeRaw.SetValue(exposure_time)
        else:
            print(
                "Exposure Time is not settable, continuing with current exposure time."
            )

    def saveImage(self, filename):
        """Function to save an image from a camera device and save it to a location.

        Overwrites any existing file at filename.
        Parameters
        ----------
        filename : str
            Path to location where the image will be saved.

        """
        # The parameter MaxNumBuffer can be used to control the count of buffers
        # allocated for grabbing. The default value of this parameter is 10.
        self.camera.MaxNumBuffer = 1

        #
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
                print("Filesaved as : {}".format(filename))
            else:
                print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
        grabResult.Release()

    def close(self):
        """If open, close access to camera.
        """
        if self.camera.IsOpen():
            self.camera.Close()
        else:
            print("Camera is already closed.")

    def __del__(self):
        self.close()
