from __future__ import print_function, division
from contextlib import contextmanager

import inspect
import os
import os.path

import warnings
from vfr.conf import (
    POS_REP_CAMERA_IP_ADDRESS,
    MET_CAL_CAMERA_IP_ADDRESS,
    MET_HEIGHT_CAMERA_IP_ADDRESS,
    PUPIL_ALGN_CAMERA_IP_ADDRESS,
    MET_CAL_MEASUREMENT_PARS,
)

import ImageAnalysisFuncs  # used to look up images

# here a nice explanation how the context managers work:
# https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/


def switch_fibre_backlight(state, manual_lamp_control=False):
    print ("switch state of backlight to %r and presse <enter>" % state)


def switch_fibre_backlight_voltage(voltage, manual_lamp_control=False):
    print ("switch voltage of backlight to %3.1f and presse <enter>" % voltage)


def switch_ambientlight(state, manual_lamp_control=False):
    print ("switch state of ambient light to %r and presse <enter>" % state)


def switch_silhouettelight(state, manual_lamp_control=False):
    print ("switch state of silhouette light to %r and presse <enter>" % state)


@contextmanager
def use_silhouettelight(manual_lamp_control=False):
    switch_silhouettelight("on", manual_lamp_control=manual_lamp_control)
    time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
    try:
        yield None

    finally:
        switch_silhouettelight("off", manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)


@contextmanager
def use_backlight(voltage, manual_lamp_control=False):
    switch_fibre_voltage(voltage, manual_lamp_control=manual_lamp_control)
    switch_fibre_backlight("on", manual_lamp_control=manual_lamp_control)
    time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
    try:
        yield None

    finally:
        switch_fibre_backlight("off", manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)


@contextmanager
def use_ambientlight(manual_lamp_control=False):
    switch_ambientlight("on", manual_lamp_control=manual_lamp_control)
    time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
    try:
        yield None

    finally:
        switch_ambientlight("off", manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)


def turntable_safe_goto(gd, grid_state, stage_position):
    print ("issuing findDatum:")
    gd.findDatum(grid_state, timeout=DATUM_TIMEOUT_DISABLE)
    print ("findDatum finished")

    print ("moving turntable to position %5.2f" % stage_position)


def safe_home_turntable(gd, grid_state):
    print ("issuing findDatum:")
    gd.findDatum(grid_state, timeout=DATUM_TIMEOUT_DISABLE)
    print ("findDatum finished")

    print ("moving turntable to home position")


def home_linear_stage():
    print ("\tHoming linear stage...", end=" ")
    print ("homed")


def linear_stage_goto(stage_position):
    print ("Found APT controller S/N", "[MOCKUP]")
    print ("\tNew position: %.2fmm %s" % (stage_position, "mm"))
    print ("\tStatus:", "OK")


class GigECamera:
    def __init__(self, conf):
        self.conf = conf

    def SetExposureTime(exposure_time_ms):
        self.exposure_time_ms = exposure_time_ms

    def saveImage(self, image_path):
        """This simulates the camera capturing an image and
        saving it to image_path, by creating a symbolic link
        from a matching test image to the requested path.
        
        The linked image is selected according to
        the IP address of the 'camera'.
        
        """
        ip_address = self.conf["IpAddress"]

        if ip_address == POS_REP_CAMERA_IP_ADDRESS:
            iname == "PT25_posrep_1_001.bmp"

        elif ip_address == MET_CAL_CAMERA_IP_ADDRESS:
            if (
                self.exporure_time_ms
                == MET_CAL_MEASUREMENT_PARS["METROLOGY_CAL_FIBRE_EXPOSURE_MS"]
            ):
                warnings.warn(
                    "using target image in place of fibre image for met "
                    "cal picture. This can't work! replace this!!"
                )
                iname = "PT25_metcal_1_001.bmp"
            else:
                iname = "PT25_metcal_1_001.bmp"

        elif ip_address == MET_HEIGHT_CAMERA_IP_ADDRESS:
            iname = "PT25_metht_1_003.bmp"

        elif ip_address == PUPIL_ALGN_CAMERA_IP_ADDRESS:
            warnings.warn(
                "setting surrogate image file for hardware simulation."
                " This can't work! replace this!!"
            )
            iname = "PT25_metht_1_003.bmp"

        # we look up the folder with the images by referencing
        # the image analysis module, and getting its location
        test_image_folder = os.path.dirname(inspect.getsourcefile(ImageAnalysisFuncs))
        mock_image_path = os.path.join(test_image_folder, "TestImages", iname)
        os.symlink(mock_image_path, image_path)
