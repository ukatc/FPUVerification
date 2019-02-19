from __future__ import print_function, division

import os
from os import path
from numpy import zeros, nan
from protectiondb import ProtectionDB as pdb
from vfr,conf import POS_REP_POSN_N, POS_REP_CAMERA_IP_ADDRESS, NR360_SERIALNUMBER

from vfr.db import save_test_result, TestResult
from vfr import turntable

from interval import Interval
from GigE.GigECamera import DEVICE_CLASS, BASLER_DEVICE_CLASS, IP_ADDRESS



from FpuGridDriver import (CAN_PROTOCOL_VERSION, SEARCH_CLOCKWISE, SEARCH_ANTI_CLOCKWISE,
                           DEFAULT_WAVEFORM_RULSET_VERSION, DATUM_TIMEOUT_DISABLE,
                           DASEL_BOTH, DASEL_ALPHA, DASEL_BETA, REQD_ANTI_CLOCKWISE,  REQD_CLOCKWISE,
                           # see documentation reference for Exception hierarchy
                           # (for CAN protocol 1, this is section 12.6.1)
                           EtherCANException, MovementError, CollisionError, LimitBreachError, FirmwareTimeoutError,
                           AbortMotionError, StepTimingError, InvalidStateException, SystemFailure,
                           InvalidParameterError, SetupError, InvalidWaveformException, ConnectionFailure,
                           SocketFailure, CommandTimeout, ProtectionError, HardwareProtectionError)

from fpu_commands import gen_wf
from fpu_constants import ALPHA_MIN_DEGREE, ALPHA_MAX_DEGREE, BETA_MIN_DEGREE, BETA_MAX_DEGREE, ALPHA_DATUM_OFFSET

from vfr.tests_common import flush, timestamp, dirac, goto_position, find_datum
import pyAPT

from ImageAnalysisFuncs.analyze_datum_repeatability import (positional_repeatability_image_analysis,
                                                            evaluate_datum_repeatability)


def  save_datum_result(env, vfdb, args, fpu_config, fpu_id, images, coords,
                       datum_repeatability_mm, datum_repeatability_has_passed):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, 'datum-repeatability')
        return keybase

    def valfunc(fpu_id):
        
                        
        val = repr({'fpuid' : fpu_id,
                    'images' : images),
                    'coords' : coords,
                    'repeatability_millimeter' : datum_repeatability_mm,
                    'result' : TestResult.OK if datum_repeatability_has_passed else TestResult.FAILED
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=args.verbosity)

    
def get_sorted_positions(fpuset, positions):
    """we need to sort the turntable angles because 
    we can only move it in rising order"""
    
    return [(fid, pos) for pos, fid in sorted((positions[fid], fid) for fid in fpuset)]


def test_datum_repeatability(env, vfdb, gd, grid_state, args, fpuset, fpu_config, 
                             DATUM_REP_ITERATIONS,
                             DATUM_REP_PASS,
                             DATUM_REP_EXPOSURE_MS):

    # home turntable

    gd.findDatum(grid_state)
    
    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        print('\tHoming stage...', end=' ')
        con.home(clockwise=True)
        print('homed')
    
    # switch backlight off
    # switch ambient light on

    # get sorted positions (this is needed because the turntable can only
    # move into one direction)
    for fpu_id, stage_position  in get_sorted_positions(fpuset, POS_REP_POSITIONS):
        # move rotary stage to POS_REP_POSN_N
        with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
            print('Found APT controller S/N', NR360_SERIALNUMBER)
            con.goto(stage_position, wait=True)
            print('\tNew position: %.2fmm %s'%(con.position(), con.unit))
            print('\tStatus:',con.status())
            
    
        # initialize pos_rep camera
        # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
        POS_REP_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                                IP_ADDRESS : POS_REP_CAMERA_IP_ADDRESS }
        
        pos_rep_cam = GigECamera(POS_REP_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(DATUM_REP_EXPOSURE_MS)
        

        unmoved_images = []
        datumed_images = []
        moved_images = []
        unmoved_coords = []
        datumed_coords = []
        moved_coords = []

        def capture_image(subtest, count):
            serialnumber = fpu_config['serialnumber']
            image_filename = "{sn}/{ts}/{tn}-{tc:%02d}-{tp}-{ic}-.bmp".format(sn=serialnumber,
                                                                              tn="datum-repeatability",
                                                                              tp=testphase,
                                                                              tc=testcount,
                                                                              ts=timestamp(),
                                                                              ic=count)
            ipath = path.join(IMAGE_FOLDER, image_filename)

            
            os.makedirs(ipath)
            pos_rep_cam.saveImage(ipath)
            
            (x, y) = positional_repeatability_image_analysis(ipath)

            return ipath, (x, y)

            
        for k in range(DATUM_REP_ITERATIONS):
            ipath, coords = capture_image("unmoved", count)
            unmoved_images.append(image_filename)
            unmoved_coords.append(coords)

    
        for k in range(DATUM_REP_ITERATIONS):
            gd.findDatum(grid_state, fpuset=[fpu_id])
            ipath, coords = capture_image("datumed", count)
            datumed_images.append(image_filename)
            datumed_coords.append(coords)
    
        gd.findDatum(grid_state)
        for k in range(DATUM_REP_ITERATIONS):
            wf = gen_wf(30 * dirac(fpu_id), 30)
            gd.configMottion(wf, grid_state)
            gd.executeMotion(grid_state, fpuset=[fpu_id])
            gd.reverseMotion(grid_state, fpuset=[fpu_id])
            gd.executeMotion(grid_state, fpuset=[fpu_id])
            gd.findDatum(grid_state, fpuset=[fpu_id])
            ipath, coords = capture_image("moved+datumed", count)
            moved_images.append(image_filename)
            moved_coords.append(coords)

        datum_repeatability_mm = evaluate_datum_repeatability(unmoved_coords, datumed_coords, moved_coords)

        datum_repeatability_has_passed = datum_repeatabilit_mm <= DATUM_REP_PASS

        images = { 'unmoved_images' : unmoved_images,
                   'datumed_images' : datumed_imaged,
                   'moved_images' : moved_images }
        
        coords = { 'unmoved_coords' : unmoved_coords,
                   'datumed_coords' : datumed_coords,
                   'moved_coords' : moved_coords }

        save_datum_result(env, vfdb, args, fpu_config, fpu_id, images, coords,
                          datum_repeatability_mm, datum_repeatability_has_passed)
        



