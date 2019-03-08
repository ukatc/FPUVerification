from __future__ import print_function, division

import os
from os import path
from numpy import zeros, nan
from protectiondb import ProtectionDB as pdb
from vfr.conf import POS_REP_POSN_N, POS_REP_CAMERA_IP_ADDRESS, NR360_SERIALNUMBER

from vfr.db.metrology_height import (env,
                                     TestResult,
                                     save_metrology_height_images,
                                     get_metrology_height_images,
                                     save_metrology_height_result)

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

from Lamps.lctrl import (switch_backlight,
                         switch_ambientlight,
                         switch_fibre_backlight_voltage,
                         use_silhouettelight)

import pyAPT

from ImageAnalysisFuncs.analyze_metrology_height import (methtHeight,
                                                         eval_met_height_inspec, 
                                                         METROLOGY_HEIGHT_ANALYSIS_ALGORITHM_VERSION)


    

def measure_metrology_height(env, vfdb, gd, grid_state, opts, fpuset, fpu_config, 
                                  MET_HEIGHT_POSITIONS=None,
                                  MET_HIGHT_TARGET_EXPOSURE_MS=None):

    tstamp=timestamp()
    
    # home turntable
    safe_home_turntable(gd, grid_state)    

    switch_backlight("off", manual_lamp_control=opts.manual_lamp_control)
    switch_ambientlight("off", manual_lamp_control=opts.manual_lamp_control)
    switch_fibre_backlight_voltage(0.0, manual_lamp_control=opts.manual_lamp_control)

    with use_silhouettelight(manual_lamp_control=opts.manual_lamp_control):

        MET_HEIGHT_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                                   IP_ADDRESS : MET_HEIGHT_CAMERA_IP_ADDRESS }
        
        met_height_cam = GigECamera(MET_HEIGHT_CAMERA_CONF)
    
        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position  in get_sorted_positions(fpuset, METROLOGY_HEIGHT_POSITIONS):
            # move rotary stage to POS_REP_POSN_N
            turntable_safe_goto(gd, grid_state, stage_position)            
        
            # initialize pos_rep camera
            # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
            
    
    
            def capture_image(camera):
    
                ipath = store_image(camera,
                                    "{sn}/{tn}/{ts}.bmp",
                                    sn=fpu_config[fpu_id]['serialnumber'],
                                    tn="metrology-height",
                                    ts=tstamp)
                
                return ipath
    
                
                       
            images = capture_image(met_height_cam)
    
    
            save_metrology_height_images(env, vfdb, opts, fpu_config, fpu_id, images)



def eval_metrology_height(env, vfdb, gd, grid_state, opts, fpuset, fpu_config,
                          met_height_analysis_pars, met_height_evaluation_pars):

    for fpu_id in fpuset:
        image = get_metrology_height_images(env, vfdb, opts, fpu_config, fpu_id)


        try:
            
            metht_small_target_height, metht_large_target_height = methtHeight(image,  **met_height_analysis_pars)


            result_in_spec = eval_met_height_inspec(metht_small_target_height,
                                                    metht_large_target_height, **met_height_evaluation_pars)

            result = TestResult.OK if result_in_spec else TestResult.FAILED
            
            errmsg = None
            
        except ImageAnalysisError as e:
            errmsg = str(e)
            metht_small_target_height = NaN
            metht_large_target_height = NaN
            result = TestResult.NA
            

        save_metrology_height_result(env, vfdb, opts, fpu_config, fpu_id,
                                     metht_small_target_height=metht_small_target_height,
                                     metht_large_target_height= metht_large_target_height
                                     test_result=testResult,
                                     errmsg=errmsg,
                                     analysis_version=METROLOGY_HEIGHT_ANALYSIS_ALGORITHM_VERSION)
        



