"""

Test moving the turntable and making exposures with the camera
at the same time using threads.

"""
from __future__ import absolute_import, division, print_function

import logging
import threading
import time
from os.path import abspath

from vfr.hw import GigECamera, lampController, pyAPT
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
    NR360_SERIALNUMBER,
    MTS50_SERIALNUMBER,
#    COLDECT_POSITIONS,
    METROLOGY_CAL_POSITIONS,
#    MET_HEIGHT_POSITIONS,
#    PUP_ALGN_POSITIONS
)

CAMERA_EXPOSURE_MS=200
STEP_TIME_MS=250
NIMAGES = 10

def initialize_lamps(lctrl):
    # switch lamps off
    lctrl.switch_all_off()

def turntable_home( clockwise=False ):
    logger = logging.getLogger(__name__)
    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        logger.info("Homing stage...")
        con.home(clockwise)

def turntable_goto( stage_position, wait=True ):
    logger = logging.getLogger(__name__)
    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        logger.info("Moving stage to %f ..." % stage_position)
        con.goto(stage_position, wait=wait)


def linear_stage_home( ):
    logger = logging.getLogger(__name__)
    with rig.hw.pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        logger.info("Homing stage...")
        con.home()

def linear_stage_goto( stage_position, wait=True ):
    logger = logging.getLogger(__name__)
    with rig.hw.pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        logger.info("Moving stage to %f ..." % stage_position)
        con.goto(stage_position, wait=wait)


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

def test_turntable( sleep_time ):
    
    print("Homing turntable ...")
    turntable_home()
    
    for stage_position in METROLOGY_CAL_POSITIONS:
        print("Moving turntable to %f ..." % stage_position)
        turntable_goto(stage_position)
        time.sleep( sleep_time )
    print("Turntable move completed.")

def test_pos_rep_camera( strategy ):
    tstamp = timestamp()
    logger = logging.getLogger(__name__)
    logger.info("Capturing positional repeatability image(s)")

    sleep_time_ms = max(0, STEP_TIME_MS - CAMERA_EXPOSURE_MS)

    print("Setting up camera.")
    pos_rep_cam = prepare_cam(CAMERA_EXPOSURE_MS)

    def capture_image( index, strategy ):
        if strategy == 1:
            ipath = store_image(
                pos_rep_cam,
                "{tn}_{ts}_camera_test.bmp",
                tn="positional-repeatability",
                ts=tstamp,
            )
        elif strategy == 2:
            ipath = store_burst_images(
                pos_rep_cam, NIMAGES, sleep_time_ms,
                "{tn}_{ts}_camera_burst_test.bmp",
                tn="positional-repeatability",
                ts=tstamp,
            )
        elif strategy == 3:
            ipath = store_one_by_one(
                pos_rep_cam, NIMAGES, STEP_TIME_MS,
                "{tn}_{ts}_camera_obo_test.bmp",
                tn="positional-repeatability",
                ts=tstamp,
            )
        else:
            logger.error("Undefined strategy: %d" % strategy )

        return ipath

    print("Capturing %d images" % NIMAGES)
    ipath = capture_image( 1, strategy )
    logger.info( "Saving image(s) to %r" % abspath(ipath) )
            

if __name__ == "__main__":
        
    lctrl = lampController()
    
    print("Starting tests")

    print("Switching lamps off")
    initialize_lamps(lctrl)

    print("Ambient light on.")
    #lctrl.use_ambientlight()
    lctrl.switch_ambientlight("on")

    x = threading.Thread(target=test_turntable, args=(0.5,))
    y = threading.Thread(target=test_pos_rep_camera, args=(2,))
    x.start()
    y.start()    
    print("Waiting for turntable thread to finish")
    x.join()
    print("Waiting for camera thread to finish")
    y.join()
    
    print("Switching lamps off")
    initialize_lamps(lctrl)
    print("Tests finished")
