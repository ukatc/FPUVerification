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

from ImageAnalysisFuncs.analyze_metrology_calibration import (metrology_calibration_find_targets,
                                                              metrology_calibration_find_fibre,
                                                              fibre_target_distance )


def  save_metrology_calibration_images(env, vfdb, args, fpu_config, fpu_id, images):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, 'metrology-calibration', 'images')
        return keybase

    def valfunc(fpu_id):
        
                        
        val = repr({'fpuid' : fpu_id,
                    'images' : images),
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=args.verbosity)


def  get_metrology_calibration_images(env, vfdb, args, fpu_config, fpu_id):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, 'metrology-calibration', 'images')
        return keybase

    return get_test_result(env, vfdb, fpuset, keyfunc, verbosity=args.verbosity)
    
    
def  save_metrology_calibration_result(env, vfdb, args, fpu_config, fpu_id,
                                       coords=None, fibre_distance=None):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, 'metrology-calibration', 'result')
        return keybase

    def valfunc(fpu_id):
        
                        
        val = repr({'fpuid' : fpu_id,
                    'coords' : coords,
                    'fibre_distance' : fibre_distance,
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=args.verbosity)
    

def measure_metrology_calibration(env, vfdb, gd, grid_state, args, fpuset, fpu_config, 
                                  METROLOGY_CAL_POSITIONS=None,
                                  METROLOGY_CAL_BACKLIGHT_VOLTAGE=None,
                                  METROLOGY_CAL_TARGET_EXPOSURE_MS=None,
                                  METROLOGY_CAL_FIBRE_EXPOSURE_MS=None):

    # home turntable
    safe_home_turntable(gd, grid_state)    

    switch_backlight("off")
    switch_ambientlight("off")
    switch_fibre_backlight_voltage(0.0)

    MET_CAL_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                            IP_ADDRESS : MET_CAL_CAMERA_IP_ADDRESS }
        
    met_cal_cam = GigECamera(MET_CAL_CAMERA_CONF)

    MET_HEIGHT_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                               IP_ADDRESS : MET_CAL_CAMERA_IP_ADDRESS }
    
    met_height_cam = GigECamera(MET_HEIGHT_CAMERA_CONF)

    # get sorted positions (this is needed because the turntable can only
    # move into one direction)
    for fpu_id, stage_position  in get_sorted_positions(fpuset, METROLOGY_CAL_POSITIONS):
        # move rotary stage to POS_REP_POSN_N
        turntable_safe_goto(gd, grid_state, stage_position)            
    
        # initialize pos_rep camera
        # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
        


        def capture_image(camera, subtest):

            ipath = store_image(camera,
                                "{sn}/{tn}/{ts}/{tp}-{tc:%02d}.bmp",
                                sn=fpu_config['serialnumber'],
                                tn="metrology-calibration",
                                ts=timestamp(),
                                tp=testphase,
                                tc=testcount)
            
            return ipath

            
        
        met_cal_cam.SetExposureTime(METROLOGY_CAL_TARGET_EXPOSURE_MS)
        switch_backlight("off")
        switch_ambientlight("on")
        switch_fibre_backlight_voltage(0.0)
        target_ipath = capture_image(met_cal_cam, "target")

    
        met_cal_cam.SetExposureTime(METROLOGY_CAL_FIBRE_EXPOSURE_MS)
        switch_backlight("off")
        switch_ambientlight("off")
        switch_fibre_backlight_voltage(METROLOGY_CAL_BACKLIGHT_VOLTAGE)
        fibre_ipath = capture_image(met_cal_cam, "fibre")

        images = { 'target' : target_ipath,
                   'fibre' : fibre_ipath }

        save_metrology_calibration_images(env, vfdb, args, fpu_config, fpu_id, images)



def eval_metrology_calibration(env, vfdb, gd, grid_state, args, fpuset, fpu_config,
                               pos_rep_analysis_pars, met_cal_analysis_pars):

    for fpu_id in fpuset:
        images = get_metrology_calibration_images(env, vfdb, args, fpu_config, fpu_id, images)


        target_coordinates = positional_repeatability_image_analysis(images['target'], **pos_rep_analysis_pars)
        fibre_coordinates = metrology_calibration_image_analysis(images['fibre'], **met_cal_analysis_pars)

        
        
        coords = { 'target_small' : target_coordinates[0],
                   'target_big' : target_coordinates[1],
                   'fibre' : fibre_coordinates }

        fibre_distance = fibre_target_distance(target_coordinates[0], target_coordinates[0], fibre_coordinates)

        save_metrology_calibration_result(env, vfdb, args, fpu_config, fpu_id, coords=coords,
                                          fibre_distance=fibre_distance)
        



