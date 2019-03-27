from __future__ import absolute_import, division, print_function

import inspect
import os
import os.path
import time
import warnings
from contextlib import contextmanager

import ImageAnalysisFuncs  # used to look up images
from FpuGridDriver import DATUM_TIMEOUT_DISABLE
from vfr.conf import (
    LAMP_WARMING_TIME_MILLISECONDS,
    MET_CAL_CAMERA_IP_ADDRESS,
    MET_CAL_MEASUREMENT_PARS,
    MET_HEIGHT_CAMERA_IP_ADDRESS,
    POS_REP_CAMERA_IP_ADDRESS,
    PUP_ALGN_CAMERA_IP_ADDRESS,
)
from vfr.tests_common import find_datum

# here a nice explanation how the context managers work:
# https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/


class lampController:
    def __init__(self):
        print("initializing mocked-up lamp controller...")

    def switch_fibre_backlight(self, state, manual_lamp_control=False):
        print("'switch state of backlight to %r and presse <enter>'" % state)


    def switch_fibre_backlight_voltage(self, voltage, manual_lamp_control=False):
        print("'switch voltage of backlight to %3.1f and presse <enter>'" % voltage)

    def switch_ambientlight(self, state, manual_lamp_control=False):
        print("'switch state of ambient light to %r and presse <enter>'" % state)

    def switch_silhouettelight(self, state, manual_lamp_control=False):
        print("'switch state of silhouette light to %r and presse <enter>'" % state)

    @contextmanager
    def use_silhouettelight(self, manual_lamp_control=False):
        self.switch_silhouettelight("on", manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
        try:
            yield None

        finally:
            self.switch_silhouettelight("off", manual_lamp_control=manual_lamp_control)
            time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)

    @contextmanager
    def use_backlight(self, voltage, manual_lamp_control=False):
        self.switch_fibre_backlight_voltage(voltage, manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
        try:
            yield None

        finally:
            self.switch_fibre_backlight("off", manual_lamp_control=manual_lamp_control)
            time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)

    @contextmanager
    def use_ambientlight(self, manual_lamp_control=False):
        self.switch_ambientlight("on", manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
        try:
            yield None

        finally:
            self.switch_ambientlight("off", manual_lamp_control=manual_lamp_control)
            time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)


def turntable_safe_goto(gd, grid_state, stage_position, opts=None):
    find_datum(gd, grid_state, opts=opts)

    print("moving turntable to position %5.2f" % stage_position)


def safe_home_turntable(gd, grid_state, opts=None):
    if (opts is not None) and opts.verbosity > 2:
        print("issuing findDatum:")
    # gd.findDatum(grid_state, timeout=DATUM_TIMEOUT_DISABLE)
    find_datum(gd, grid_state, opts=opts)
    if (opts is not None) and opts.verbosity > 2:
        print("findDatum finished")

    print("moving turntable to home position")


def home_linear_stage():
    print("\tHoming linear stage...", "end=' '")
    print("homed")


def linear_stage_goto(stage_position):
    print("Found APT controller S/N", "[MOCKUP]")
    print("\tNew position: %.2fmm %s" % (stage_position, "mm"))
    print("\tStatus:", "OK")


class GigECamera:
    def __init__(self, conf):
        self.conf = conf

    def SetExposureTime(self, exposure_time_ms):
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
            iname = "PT25_posrep_1_001.bmp"

        elif ip_address == MET_CAL_CAMERA_IP_ADDRESS:
            if (
                self.exposure_time_ms
                == MET_CAL_MEASUREMENT_PARS.METROLOGY_CAL_FIBRE_EXPOSURE_MS
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

        elif ip_address == PUP_ALGN_CAMERA_IP_ADDRESS:
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
