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

from vfr.tests_common import (flush, timestamp, dirac, goto_position, find_datum, store_image,
                              get_sorted_positions, safe_home_turntable)

from Lamps.lctrl import switch_backlight, switch_ambientlight

import pyAPT

from ImageAnalysisFuncs.analyze_positional_repeatability import (positional_repeatability_image_analysis,
                                                            evaluate_positional_repeatability)


def  save_positional_repeatability_images(env, vfdb, args, fpu_config, fpu_id, images):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, 'positional-repeatability', 'images')
        return keybase

    def valfunc(fpu_id):
        
                        
        val = repr({'fpuid' : fpu_id,
                    'images' : images),
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=args.verbosity)


def  get_positional_repeatability_images(env, vfdb, args, fpu_config, fpu_id):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, 'positional-repeatability', 'images')
        return keybase

    return get_test_result(env, vfdb, fpuset, keyfunc, verbosity=args.verbosity)
    
    
def  save_positional_repeatability_result(env, vfdb, args, fpu_config, fpu_id, coords=None,
                                     positional_repeatability_mm=None,
                                     positional_repeatability_has_passed=None):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, 'positional-repeatability', 'result')
        return keybase

    def valfunc(fpu_id):
        
                        
        val = repr({'fpuid' : fpu_id,
                    'coords' : coords,
                    'repeatability_millimeter' : positional_repeatability_mm,
                    'result' : TestResult.OK if positional_repeatability_has_passed else TestResult.FAILED
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=args.verbosity)
    

def measure_positional_repeatability(env, vfdb, gd, grid_state, args, fpuset, fpu_config, 
                                     POSITIONAL_REP_ITERATIONS=None,
                                     POSITION_REP_POSITIONS=None,
                                     POSITION_REP_INCREMENTS=None,
                                     POSITIONAL_REP_EXPOSURE_MS=None):

    # home turntable
    safe_home_turntable(gd, grid_state)    

    switch_backlight("off")
    switch_ambientlight("on")
    switch_fibre_backlight_voltage(0.0)

    # get sorted positions (this is needed because the turntable can only
    # move into one direction)
    for fpu_id, stage_position  in get_sorted_positions(fpuset, POS_REP_POSITIONS):
        # move rotary stage to POS_REP_POSN_N
        turntable_safe_goto(gd, grid_state, stage_position)            
    
        # initialize pos_rep camera
        # set pos_rep camera exposure time to POSITIONAL_REP_EXPOSURE milliseconds
        POS_REP_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                                IP_ADDRESS : POS_REP_CAMERA_IP_ADDRESS }
        
        pos_rep_cam = GigECamera(POS_REP_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(POSITIONAL_REP_EXPOSURE_MS)
        

        unmoved_images = []
        datumed_images = []
        moved_images = []

        def capture_image(subtest, count):

            ipath = store_image(pos_rep_cam,
                                "{sn}/{tn}/{ts}/{tp}-{tc:%02d}-{ic:%03d}-.bmp",
                                sn=fpu_config['serialnumber'],
                                tn="positional-repeatability",
                                ts=timestamp(),
                                tp=testphase,
                                tc=testcount,
                                ic=count)
            
            return ipath

            
        for k in range(POSITIONAL_REP_ITERATIONS):
            ipath = capture_image("unmoved", count)
            unmoved_images.append(ipath)

    
        for k in range(POSITIONAL_REP_ITERATIONS):
            gd.findDatum(grid_state, fpuset=[fpu_id])
            ipath = capture_image("positionaled", count)
            positionaled_images.append(ipath)
    
        gd.findDatum(grid_state)
        for k in range(POSITIONAL_REP_ITERATIONS):
            wf = gen_wf(30 * dirac(fpu_id), 30)
            gd.configMottion(wf, grid_state)
            gd.executeMotion(grid_state, fpuset=[fpu_id])
            gd.reverseMotion(grid_state, fpuset=[fpu_id])
            gd.executeMotion(grid_state, fpuset=[fpu_id])
            gd.findDatum(grid_state, fpuset=[fpu_id])
            ipath, coords = capture_image("moved+positionaled", count)
            moved_images.append(ipath)

        images = { 'unmoved_images' : unmoved_images,
                   'positionaled_images' : positionaled_imaged,
                   'moved_images' : moved_images }
        

        save_positional_repeatability_images(env, vfdb, args, fpu_config, fpu_id, images)



def eval_positional_repeatability(env, vfdb, gd, grid_state, args, fpuset, fpu_config,
                                  pos_rep_analysis_pars, pos_rep_evaluation_pars):

    for fpu_id in fpuset:
        images = get_positional_repeatability_images(env, vfdb, args, fpu_config, fpu_id, images)

        def analysis_func(ipath):
            return positional_repeatability_image_analysis(ipath, **pos_rep_analysis_pars)
        

        unmoved_coords = map(analysis_func, images['inmoved_images'])
        positionaled_coords = map(analysis_func, images['positionaled_images'])
        moved_coords = map(analysis_func, images['moved_images'])
        
        
        positional_repeatability_mm = evaluate_positional_repeatability(unmoved_coords, positionaled_coords, moved_coords)

        positional_repeatability_has_passed = positional_repeatability_mm <= POSITIONAL_REP_PASS
        
        coords = { 'unmoved_coords' : unmoved_coords,
                   'positionaled_coords' : positionaled_coords,
                   'moved_coords' : moved_coords }

        save_positional_repeatability_result(env, vfdb, args, fpu_config, fpu_id, coords=coords,
                                        positional_repeatability_mm=positional_repetability_mm,
                                        positional_repeatability_has_passed=positional_repetability_has_passed)
        



