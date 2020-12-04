"""

Test moving the turntable and making exposures with the camera
at the same time using threads.

"""
from __future__ import absolute_import, division, print_function

import logging
import multiprocessing as mp
import time
from os.path import abspath

import os
import argparse

import FpuGridDriver
from FpuGridDriver import  DASEL_BOTH, DASEL_ALPHA, DASEL_BETA, \
    SEARCH_CLOCKWISE, SEARCH_ANTI_CLOCKWISE, SEARCH_AUTO, SKIP_FPU, \
    REQD_CLOCKWISE, REQD_ANTI_CLOCKWISE, DATUM_TIMEOUT_DISABLE

from fpu_commands import *
from fpu_constants import MOTOR_MIN_STEP_FREQUENCY, MOTOR_MAX_STEP_FREQUENCY, \
    MOTOR_MAX_START_FREQUENCY, MAX_STEP_DIFFERENCE, MOTOR_MAX_ACCELERATION, \
    MOTOR_MAX_DECELERATION, MAX_ACCELERATION_FACTOR, WAVEFORM_SEGMENT_LENGTH_MS
    
import wflib

#NUM_FPUS = int(os.environ.get("NUM_FPUS","7"))
NUM_FPUS = 1
FPU_ID = 0
GATEWAY_ADDRESS = "192.168.0.11"
GATEWAY_PORT = 4700
PATH_FILE = "/home/jnix/targets_19fp_case_1_PATHS.paths"
CANMAP_FILE = "canmap1_15.cfg"

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

CAMERA_EXPOSURE_MS=64
STEP_TIME_MS=200
NIMAGES = 512
NREPEATS = 1

# NOTE: Turntable positions must be in numerical order.
# The turntable can only move in one direction, and then needs to be homed.
#METROLOGY_CAL_POSITIONS = [254.0, 314.5, 13.0, 73.0, 133.5]
TURNTABLE_POSITIONS = [133.5, 254.0]

def initialize_FPU(nfpus, gateway, port=4700, min_step_frequency=490,
                   max_step_frequency=MOTOR_MAX_STEP_FREQUENCY,
                   max_start_frequency=MOTOR_MAX_START_FREQUENCY,
                   max_acceleration=1.6, mockup=False, resetFPU=False):
    
    gd = FpuGridDriver.GridDriver(nfpus,
                                  motor_minimum_frequency=min_step_frequency,  
                                  motor_maximum_frequency=max_step_frequency, 
                                  motor_max_start_frequency=max_start_frequency,
                                  motor_max_rel_increase=max_acceleration)

    if mockup:
        gateway_address = [ FpuGridDriver.GatewayAddress("127.0.0.1", p)
                            for p in [4700, 4701, 4702] ]
    else:
        gateway_address = [ FpuGridDriver.GatewayAddress(gateway, port) ]

    print("Connecting grid:", gd.connect(address_list=gateway_address))


    # We monitor the FPU grid by a variable which is
    # called grid_state, and reflects the state of
    # all FPUs.
    grid_state = gd.getGridState()

    if resetFPU:
        print("Resetting FPU")
        gd.resetFPUs(grid_state)
        print("OK")

    return gd, grid_state


def initialize_lamps(lctrl):
    # switch lamps off
    lctrl.switch_all_off()

def turntable_home( ):
    logger = logging.getLogger(__name__)
    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        logger.info("Homing stage...")
        con.home(clockwise=False)

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
    
    for rep in range(0, NREPEATS):
        for stage_position in TURNTABLE_POSITIONS:
            print("Moving turntable to %f ..." % stage_position)
            turntable_goto(stage_position)
            time.sleep( sleep_time )
        print("Turntable move completed.")

        print("Homing turntable ...")
        turntable_home()

def test_fpu( gd, gs, wf ):
    time.sleep(4.0)
    gd.configPaths(p, gs, fpuset=[FPU_ID])
    gd.executeMotion(gs)
    time.sleep(3.0)
    gd.reverseMotion(gs)
    gd.executeMotion(gs)

def test_pos_rep_camera( strategy ):
    tstamp = timestamp()
    logger = logging.getLogger(__name__)
    logger.info("Capturing path tracking image(s)")

    sleep_time_ms = max(0, STEP_TIME_MS - CAMERA_EXPOSURE_MS)

    print("Setting up camera.")
    pos_rep_cam = prepare_cam(CAMERA_EXPOSURE_MS)

    def capture_image( index, strategy ):
        if strategy == 1:
            ipath = store_image(
                pos_rep_cam,
                "{tn}_{ts}_oneshot.bmp",
                tn="path-tracking",
                ts=tstamp,
            )
        elif strategy == 2:
            ipath = store_burst_images(
                pos_rep_cam, NIMAGES, sleep_time_ms,
                "{tn}_{ts}_burst.bmp",
                tn="path-tracking",
                ts=tstamp,
            )
        elif strategy == 3:
            ipath = store_one_by_one(
                pos_rep_cam, NIMAGES, STEP_TIME_MS,
                "{tn}_{ts}_obo.bmp",
                tn="path-tracking",
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

    print("Setting up turntable.")
    turntable_home()
    turntable_goto(METROLOGY_CAL_POSITIONS[4])

    print("Ambient light on.")
    lctrl.switch_ambientlight("on")

    print("Initializing FPUs")
    gd, gs = initialize_FPU(NUM_FPUS, GATEWAY_ADDRESS, GATEWAY_PORT)
    print("Datuming FPUs and moving to zero position")
    #gd.findDatum(gs, timeout=DATUM_TIMEOUT_DISABLE)
    gd.findDatum(gs)
    gd.configZero(gs)
    gd.executeMotion(gs)
    
    print("Reading paths")
    p = wflib.load_paths(PATH_FILE, canmap_fname=CANMAP_FILE)
    
    y = mp.Process(name='camera', target=test_pos_rep_camera, args=(2,))
    y.start()    
    print("Moving FPUs in main thread")
    test_fpu(gd, gs, p)

    print("Waiting for camera thread to finish")
    y.join()

    print("Parking FPU.")
    gd.configDatum(gs)
    gd.executeMotion(gs)
    gd.findDatum(gs)
    
    print("Switching lamps off")
    initialize_lamps(lctrl)
    print("Tests finished")
