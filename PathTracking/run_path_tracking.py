"""

Measure the path taken by a fibre positioner by making continuous
exposures with the camera while the FPU is moving.

The FPU is instructed to follow the path produced by the mocpath
path analysis software and contained in a path file.

"""
from __future__ import absolute_import, division, print_function

import logging
logging.basicConfig(level=logging.INFO)   # Informational output 
#logging.basicConfig(level=logging.DEBUG)  # Debugging output

import multiprocessing as mp
import time
from os.path import abspath

import os

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
#PATH_FILE = "/home/jnix/targets_19fp_case_1_PATHS.paths"
#CANMAP_FILE = "canmap19_15.cfg"

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

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("pathfile", type=str, default="/home/jnix/targets_19fp_case_1_PATHS.paths",
                    help="Name of file (from mocpath) containing FPU paths")
parser.add_argument("canmap", type=str, default="canmap19_15.cfgs",
                    help="Name of file containing CAN ID to FPU ID mapping.")

parser.add_argument("--exposure", type=float, default=128.0,
                    help="Camera exposure time in milliseconds")
parser.add_argument("--steptime", type=float, default=200.0,
                    help="Path step time interval in milliseconds. Must be >= exposure time.")
parser.add_argument("--nimages", type=int, default=380,
                    help="Number of camera images to collect while executing path.")
parser.add_argument("-d", "--debug", action="store_true",
                    help="Run with debugging log level")

#CAMERA_EXPOSURE_MS=200
#STEP_TIME_MS=200
#NIMAGES = 380
#NREPEATS = 1

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
    slogger = logging.getLogger(__name__)
    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        slogger.info("Homing stage...")
        con.home(clockwise=False)

def turntable_goto( stage_position, wait=True ):
    slogger = logging.getLogger(__name__)
    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        slogger.info("Moving stage to %f ..." % stage_position)
        con.goto(stage_position, wait=wait)


def linear_stage_home( ):
    slogger = logging.getLogger(__name__)
    with rig.hw.pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        slogger.info("Homing stage...")
        con.home()

def linear_stage_goto( stage_position, wait=True ):
    slogger = logging.getLogger(__name__)
    with rig.hw.pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        slogger.info("Moving stage to %f ..." % stage_position)
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
    
    slogger = logging.getLogger(__name__)
    turntable_home()
    
    for rep in range(0, NREPEATS):
        for stage_position in TURNTABLE_POSITIONS:
            turntable_goto(stage_position)
            time.sleep( sleep_time )
        slogger.info("Turntable moves completed.")
        turntable_home()

def test_fpu( gd, gs, wf ):
    time.sleep(4.0)
    gd.configPaths(p, gs, fpuset=[FPU_ID])
    gd.executeMotion(gs)
    time.sleep(3.0)
    # NOTE: Reversing the motion makes it harder to determine the end point of a track.
    gd.reverseMotion(gs)
    gd.executeMotion(gs)

def test_pos_rep_camera( strategy, camera_exposure, step_time, nimages ):
    tstamp = timestamp()
    clogger = logging.getLogger(__name__)
    clogger.debug("Capturing path tracking image(s)")

    sleep_time_ms = max(0, step_time - camera_exposure)

    clogger.info("Setting up camera for exposure %.2f ms and strategy %d." % \
                (camera_exposure, strategy))
    pos_rep_cam = prepare_cam(camera_exposure)

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
                pos_rep_cam, nimages, sleep_time_ms,
                "{tn}_{ts}_burst",
                tn="path-tracking",
                ts=tstamp,
            )
        elif strategy == 3:
            ipath = store_one_by_one(
                pos_rep_cam, nimages, step_time,
                "{tn}_{ts}_obo",
                tn="path-tracking",
                ts=tstamp,
            )
        else:
            clogger.error("Undefined strategy: %d" % strategy )

        return ipath

    clogger.debug("Capturing %d images." % nimages )
    ipath = capture_image( 1, strategy ) 
    clogger.info("Captured %d images and saved to %r" % (nimages, abspath(ipath)))

if __name__ == "__main__":
    args = parser.parse_args()
    mlogger = logging.getLogger("")
    if args.debug:
        mlogger.setLevel( logging.DEBUG )
    if args.steptime < args.exposure:
        mlogger.warn("Exposure time (%f) is large than step time (%f)." % \
            (args.exposure, args.steptime))

    lctrl = lampController()

    mlogger.debug("Starting tests")

    mlogger.info("Switching lamps off")
    initialize_lamps(lctrl)

    mlogger.info("Setting up turntable.")
    turntable_home()
    turntable_goto(METROLOGY_CAL_POSITIONS[4])

    mlogger.info("Ambient light on.")
    lctrl.switch_ambientlight("on")
# Fibre backlight does not seem to work properly.
#    mlogger.info("Fibre backlight light on.")
#    lctrl.switch_fibre_backlight("on")

    mlogger.info("Initializing FPUs")
    gd, gs = initialize_FPU(NUM_FPUS, GATEWAY_ADDRESS, GATEWAY_PORT)
    mlogger.info("Datuming FPUs and moving to zero position")
    #gd.findDatum(gs, timeout=DATUM_TIMEOUT_DISABLE)
    gd.findDatum(gs)
    gd.configZero(gs)
    gd.executeMotion(gs)

    mlogger.info("Reading paths")
    p = wflib.load_paths(args.pathfile, canmap_fname=args.canmap)

    y = mp.Process(name='camera', target=test_pos_rep_camera, args=(2, args.exposure, args.steptime, args.nimages))
    y.start()
    mlogger.info("Moving FPUs in main thread")
    test_fpu(gd, gs, p)

    mlogger.info("Waiting for camera thread to finish")
    y.join()

    mlogger.info("Parking FPU.")
    gd.configDatum(gs)
    gd.executeMotion(gs)
    gd.findDatum(gs)

    mlogger.info("Switching lamps off")
    initialize_lamps(lctrl)
    mlogger.info("Tests finished")
