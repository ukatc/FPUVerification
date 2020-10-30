from __future__ import absolute_import, division, print_function

import logging
from os.path import abspath

from vfr.hw import GigECamera, lampController
from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS

from vfr.tests_common import (
#     fixup_ipath,
    store_image,
    store_burst_images,
    store_one_by_one,
    timestamp,
    safe_home_turntable,
    turntable_safe_goto,
    check_image_analyzability,
)

from vfr.conf import (
#     VERIFICATION_ROOT_FOLDER,
#     MET_CAL_CAMERA_IP_ADDRESS,
    POS_REP_CAMERA_IP_ADDRESS,
)

CAMERA_EXPOSURE_MS=200

def initialize_lamps(lctrl):
    # switch lamps off
    lctrl.switch_all_off()

def prepare_cam(exposure_time):
    # initialize pos_rep camera
    # set pos_rep camera exposure time to POSITIONAL_REP_EXPOSURE milliseconds
    POS_REP_CAMERA_CONF = {
        DEVICE_CLASS: BASLER_DEVICE_CLASS,
        IP_ADDRESS: POS_REP_CAMERA_IP_ADDRESS,
    }

    pos_rep_cam = GigECamera(POS_REP_CAMERA_CONF)
    pos_rep_cam.SetExposureTime(exposure_time)

    return pos_rep_cam


def test_pos_rep_camera(lctrl, strategy=1):
    tstamp = timestamp()
    logger = logging.getLogger(__name__)
    logger.info("Capturing positional repeatability image(s)")

    print("Switching lamps off")
    initialize_lamps(lctrl)

    with lctrl.use_ambientlight():
        print("AMbient light on. Setting up camera.")
        pos_rep_cam = prepare_cam(CAMERA_EXPOSURE_MS)

        def capture_image(index, strategy=1):
            if strategy == 1:
                ipath = store_image(
                    pos_rep_cam,
                    "{tn}_{ts}_camera_test.bmp",
                    tn="positional-repeatability",
                    ts=tstamp,
                )
            elif strategy == 2:
                ipath = store_burst_images(
                    pos_rep_cam, 10,
                    "{tn}_{ts}_camera_burst_test.bmp",
                    tn="positional-repeatability",
                    ts=tstamp,
                )
            elif strategy == 3:
                ipath = store_one_by_one(
                    pos_rep_cam, 10, 250,
                    "{tn}_{ts}_camera_obo_test.bmp",
                    tn="positional-repeatability",
                    ts=tstamp,
                )
            else:
                logger.error("Undefined strategy: %d" % strategy )

            return ipath

        print("Capturing image")
        ipath = capture_image( 1, strategy=strategy )
        logger.info( "Saving image to %r" % abspath(ipath) )
            
    logger.info("Positional repeatability image(s) captured successfully")


if __name__ == "__main__":
        
    lctrl = lampController()

    print("Starting tests")
    print("Single image")
    test_pos_rep_camera(lctrl, 1)
    print("Burst of images")
    test_pos_rep_camera(lctrl, 2)
    print("One by one burst")
    test_pos_rep_camera(lctrl, 3)
    print("Tests finished")
