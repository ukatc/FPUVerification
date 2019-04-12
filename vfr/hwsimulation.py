from __future__ import absolute_import, division, print_function

import inspect
import os
import os.path
import warnings

import ImageAnalysisFuncs  # used to look up images

from Lamps.lctrl import LampControllerBase

from vfr.conf import (
    MET_CAL_CAMERA_IP_ADDRESS,
    MET_CAL_MEASUREMENT_PARS,
    MET_HEIGHT_CAMERA_IP_ADDRESS,
    POS_REP_CAMERA_IP_ADDRESS,
    PUP_ALGN_CAMERA_IP_ADDRESS,
)
from vfr.tests_common import find_datum

# here a nice explanation how the context managers work:
# https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/


class lampController(LampControllerBase):
    def __init__(self):
        print("initializing mocked-up lamp controller...")
        self.backlight_state = 0.0
        self.ambientlight_state = 0.0
        self.silhouettelight_state = 0.0

    def switch_fibre_backlight(self, state):
        previous_state = self.backlight_state
        print("'switch state of backlight to %r and presse <enter>'" % state)
        self.backlight_state = state
        return previous_state

    def switch_fibre_backlight_voltage(self, voltage):
        previous_state = self.backlight_state
        print("'switch voltage of backlight to %3.1f and presse <enter>'" % voltage)
        self.backlight_state = voltage
        return previous_state

    def switch_ambientlight(self, state):
        previous_state = self.ambientlight_state
        print("'switch state of ambient light to %r and presse <enter>'" % state)
        self.ambientlight_state = state
        return previous_state

    def switch_silhouettelight(self, state, manual_lamp_control=False):
        previous_state = self.silhouettelight_state
        print("'switch state of silhouette light to %r and presse <enter>'" % state)
        self.silhouettelight_state = state
        return previous_state


def turntable_safe_goto(rig, grid_state, stage_position, opts=None):
    with rig.lctrl.use_ambientlight():
        find_datum(rig.gd, grid_state, opts=opts)

        print("moving turntable to position %5.2f" % stage_position)


def safe_home_turntable(rig, grid_state, opts=None):
    if (opts is not None) and opts.verbosity > 2:
        print("issuing findDatum:")
    # gd.findDatum(grid_state, timeout=DATUM_TIMEOUT_DISABLE)
    with rig.lctrl.use_ambientlight():
        find_datum(rig.gd, grid_state, opts=opts)
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
                == MET_CAL_MEASUREMENT_PARS.METROLOGY_CAL_FIBRE_EXPOSURE_MS  # # pylint: disable=no-member
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
