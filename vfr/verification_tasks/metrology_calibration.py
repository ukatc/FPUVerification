from __future__ import print_function, division

import os
from os import path
from numpy import zeros, nan
from protectiondb import ProtectionDB as pdb
from vfr.conf import POS_REP_POSN_N, POS_REP_CAMERA_IP_ADDRESS, NR360_SERIALNUMBER

from vfr.db.metrology_calibration import (env,
                                          TestResult,
                                          save_metrology_calibration_images,
                                          get_metrology_calibration_images,
                                          save_metrology_calibration_result)

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

from ImageAnalysisFuncs.analyze_metrology_calibration import (metcalTargetCoordinates,
                                                              metcalFibreCoordinates,
                                                              fibre_target_distance,
                                                              METROLOGY_ANALYSIS_ALGORITHM_VERSION)


    

def measure_metrology_calibration(env, vfdb, gd, grid_state, args, fpuset, fpu_config, 
                                  METROLOGY_CAL_POSITIONS=None,
                                  METROLOGY_CAL_BACKLIGHT_VOLTAGE=None,
                                  METROLOGY_CAL_TARGET_EXPOSURE_MS=None,
                                  METROLOGY_CAL_FIBRE_EXPOSURE_MS=None):

    tstamp=timestamp()
    
    # home turntable
    safe_home_turntable(gd, grid_state)    

    switch_backlight("off", manual_lamp_control=args.manual_lamp_control)
    switch_ambientlight("off", manual_lamp_control=args.manual_lamp_control)
    switch_fibre_backlight_voltage(0.0, manual_lamp_control=args.manual_lamp_control)

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
                                "{sn}/{tn}/{ts}/{tp}-{tc:02d}.bmp",
                                sn=fpu_config[fpu_id]['serialnumber'],
                                tn="metrology-calibration",
                                ts=tstamp,
                                tp=testphase,
                                tc=testcount)
            
            return ipath

            
        
        met_cal_cam.SetExposureTime(METROLOGY_CAL_TARGET_EXPOSURE_MS)
        switch_backlight("off", manual_lamp_control=args.manual_lamp_control)
        switch_ambientlight("on", manual_lamp_control=args.manual_lamp_control)
        switch_fibre_backlight_voltage(0.0, manual_lamp_control=args.manual_lamp_control)
        target_ipath = capture_image(met_cal_cam, "target")

    
        met_cal_cam.SetExposureTime(METROLOGY_CAL_FIBRE_EXPOSURE_MS)
        switch_backlight("off", manual_lamp_control=args.manual_lamp_control)
        switch_ambientlight("off", manual_lamp_control=args.manual_lamp_control)
        switch_fibre_backlight_voltage(METROLOGY_CAL_BACKLIGHT_VOLTAGE)
        
        fibre_ipath = capture_image(met_cal_cam, "fibre")

        images = { 'target' : target_ipath,
                   'fibre' : fibre_ipath }

        save_metrology_calibration_images(env, vfdb, args, fpu_config, fpu_id, images)



def eval_metrology_calibration(env, vfdb, gd, grid_state, args, fpuset, fpu_config,
                               pos_rep_analysis_pars, met_cal_analysis_pars):

    for fpu_id in fpuset:
        images = get_metrology_calibration_images(env, vfdb, args, fpu_config, fpu_id, images)


        try:
            target_coordinates = metcalTargetCoordinates(images['target'], **pos_rep_analysis_pars)
            fibre_coordinates = metcalFibreCoordinates(images['fibre'], **met_cal_analysis_pars)

        
        
            coords = { 'target_small_xy' : target_coordinates[0:2],
                       'target_small_q' : target_coordinates[2],
                       'target_big_xy' : target_coordinates[3:5],
                       'target_big_q' : target_coordinates[5],
                       'fibre_xy' : fibre_coordinates[0:2],
                       'fibre_q' : fibre_coordinates[2],}

            fibre_distance = fibre_target_distance(target_coordinates[0:2], target_coordinates[3:5], fibre_coordinates[0:2])
            
            errmsg = None
            
        except ImageAnalysisError as e:
            errmsg = str(e)
            coords = {}
            fibre_distance = NaN

        save_metrology_calibration_result(env, vfdb, args, fpu_config, fpu_id, coords=coords,
                                          fibre_distance=fibre_distance,
                                          errmsg=errmsg,
                                          analysis_version=METROLOGY_ANALYSIS_ALGORITHM_VERSION)
        



