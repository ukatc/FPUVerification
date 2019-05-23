from __future__ import absolute_import, division, print_function

import inspect
import os
import os.path
import warnings
import time
from contextlib import contextmanager

import ImageAnalysisFuncs  # used to look up images

from Lamps.lctrl import LampControllerBase

from vfr.conf import (
    MET_CAL_CAMERA_IP_ADDRESS,
    MET_CAL_MEASUREMENT_PARS,
    MET_HEIGHT_CAMERA_IP_ADDRESS,
    POS_REP_CAMERA_IP_ADDRESS,
    PUP_ALGN_CAMERA_IP_ADDRESS,
)

# here a nice explanation how the context managers work:
# https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/


class lampController(LampControllerBase):
    def __init__(self):
        print("HWS: initializing mocked-up lamp controller...")
        self.backlight_state = 0.0
        self.ambientlight_state = 0.0
        self.silhouettelight_state = 0.0

    def switch_fibre_backlight(self, state):
        previous_state = self.backlight_state
        print("HWS: 'switch state of backlight to %r and press <enter>'" % state)
        self.backlight_state = state
        return previous_state

    def switch_fibre_backlight_voltage(self, voltage):
        previous_state = self.backlight_state
        print("HWS: 'switch voltage of backlight to %3.1f and press <enter>'" % voltage)
        self.backlight_state = voltage
        return previous_state

    def switch_ambientlight(self, state):
        previous_state = self.ambientlight_state
        print("HWS: 'switch state of ambient light to %r and press <enter>'" % state)
        self.ambientlight_state = state
        return previous_state

    def switch_silhouettelight(self, state, manual_lamp_control=False):
        previous_state = self.silhouettelight_state
        print("HWS: 'switch state of silhouette light to %r and press <enter>'" % state)
        self.silhouettelight_state = state
        return previous_state


class StageController:
    def __init__(self, name, unit="mm"):
        self.name = name
        self.unit = unit
        self._position = 0.0

    def position(self):
        return self._position

    def status(self):
        return "OK"

    def home(self, clockwise=None):
        print("HWS: homing %s stage..." % self.name)
        self._position = 0.0
        time.sleep(1.0)
        print("HWS: stage %s is homed" % self.name)

    def goto(self, position, wait=None):
        print("HWS: moving %s stage to %f..." % (self.name, position))
        self._position = position
        time.sleep(1.0)
        print("HWS: stage %s is now at position %f" % (self.name, position))


class _pyAPT:
    @contextmanager
    def NR360S(self, serial_number=None):
        try:
            yield StageController("NR360S", unit="degrees")

        finally:
            time.sleep(1.0)

    @contextmanager
    def MTS50(self, serial_number=None):
        try:
            yield StageController("MTS50", unit="mm")

        finally:
            time.sleep(1.0)


pyAPT = _pyAPT()


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
            # we use the eposure time to discern between
            # a target and a fibre image
            if (
                self.exposure_time_ms
                == MET_CAL_MEASUREMENT_PARS.METROLOGY_CAL_FIBRE_EXPOSURE_MS  # # pylint: disable=no-member
            ):
                iname = "PT24_metcal_fibre_2019-04-09.bmp"
            else:
                iname = "PT25_metcal_1_001.bmp"

        elif ip_address == MET_HEIGHT_CAMERA_IP_ADDRESS:
            iname = "PT25_metht_1_003.bmp"

        elif ip_address == PUP_ALGN_CAMERA_IP_ADDRESS:
            iname = "PT24_pupil-alignment_2019-04-08_+010.000_-080.000.bmp"

        # we look up the folder with the images by referencing
        # the image analysis module, and getting its location
        test_image_folder = os.path.dirname(inspect.getsourcefile(ImageAnalysisFuncs))
        mock_image_path = os.path.join(test_image_folder, "TestImages", iname)
        os.symlink(mock_image_path, image_path)
