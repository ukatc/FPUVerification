from __future__ import print_function, division

import os
from os import path
from numpy import zeros, nan
from protectiondb import ProtectionDB as pdb
from vfr.conf import PUP_ALN_CAMERA_IP_ADDRESS, NR360_SERIALNUMBER

from vfr.db.pupil_alignment import (env,
                                    TestResult,
                                    save_pupil_alignment_images,
                                    get_pupil_alignment_images,
                                    save_pupil_alignment_result,
                                    get_pupil_alignment_result,
                                    get_pupil_alignment_passed_p)

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
                              get_sorted_positions, safe_home_turntable,
                              linear_stage_goto, home_linear_stage)

from Lamps.lctrl import (switch_backlight,
                         switch_ambientlight,
                         use_backlight,
                         switch_fibre_backlight_voltage,
                         use_ambientlight,
                         use_silhouettelight)

import pyAPT

from ImageAnalysisFuncs.analyze_pupil_alignment import (pupalnCoordinates, evaluate_pupil_alignment)

from ImageAnalysisFuncs.analyze_metrology_calibration import (metcalTargetCoordinates, metcalFibreCoordinates)

from ImageAnalysisFuncs.analyze_metrology_height import methtHeight

from ImageAnalysisFuncs.analyze_positional_repeatability import posrepCoordinates




        
def selftest_pup_algn(env, vfdb, gd, grid_state, opts, fpuset, fpu_config,
                      PUPIL_ALN_POSITIONS=None,
                      PUPIL_ALN_LINPOSITIONS=None,
                      PUPIL_ALN_EXPOSURE_MS=None,
                      PUPALGN_CALIBRATION_PARS=None,
                      PUPALGN_ANALYSIS_PARS=None,
                      capture_image=None,
                      **kwargs):
    try:
        # home turntable
        safe_home_turntable(gd, grid_state)    
        home_linear_stage()    

        switch_ambientlight("off", manual_lamp_control=opts.manual_lamp_control)
        switch_silhouettelight("off", manual_lamp_control=opts.manual_lamp_control)
        
        with use_backlight(5.0, manual_lamp_control=opts.manual_lamp_control):
    
            # initialize pos_rep camera
            # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
            PUP_ALN_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                                    IP_ADDRESS : PUP_ALN_CAMERA_IP_ADDRESS }
            
            pup_aln_cam = GigECamera(PUP_ALN_CAMERA_CONF)
            pup_aln_cam.SetExposureTime(PUPIL_ALN_EXPOSURE_MS)

                
            fpu_id, stage_position =  get_sorted_positions(fpuset, PUP_ALN_POSITIONS)[0]
            
            # move rotary stage to PUP_ALN_POSN_N
            turntable_safe_goto(gd, grid_state, stage_position)            
            linear_stage_goto(PUPIL_ALN_LINPOSITIONS[fpu_id])            
            
            ipath_selftest_pup_algn = capture_image(pup_aln_cam, "pupil-alignment")
            
            #gd.findDatum(grid_state, fpuset=[fpu_id])
            
            result = pupalnCoordinates(ipath_selftest_pup_algn,
                                       PUPALGN_CALIBRATION_PARS=PUPALGN_CALIBRATION_PARS,
                                       **PUPALGN_ANALYSIS_PARS)
    finally:
        safe_home_turntable(gd, grid_state)    
        home_linear_stage()    





def selftest_metrology_calibration(env, vfdb, gd, grid_state, opts, fpuset, fpu_config,
                                   METROLOGY_CAL_POSITIONS=None,
                                   METROLOGY_CAL_BACKLIGHT_VOLTAGE=None,
                                   METROLOGY_CAL_TARGET_EXPOSURE_MS=None,
                                   METROLOGY_CAL_FIBRE_EXPOSURE_MS=None,
                                   METCAL_TARGET_ANALYSIS_PARS=None,
                                   METCAL_FIBRE_ANALYSIS_PARS=None,
                                   capture_image=None):

    try:
        # home turntable
        safe_home_turntable(gd, grid_state)    
    
        switch_backlight("off", manual_lamp_control=opts.manual_lamp_control)
        switch_ambientlight("off", manual_lamp_control=opts.manual_lamp_control)
        switch_fibre_backlight_voltage(0.0, manual_lamp_control=opts.manual_lamp_control)
    
        MET_CAL_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                                IP_ADDRESS : MET_CAL_CAMERA_IP_ADDRESS }
            
        met_cal_cam = GigECamera(MET_CAL_CAMERA_CONF)
    
        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        fpu_id, stage_position  in get_sorted_positions(fpuset, METROLOGY_CAL_POSITIONS)[0]
        
        # move rotary stage to POS_REP_POSN_0
        turntable_safe_goto(gd, grid_state, stage_position)            
            
        met_cal_cam.SetExposureTime(METROLOGY_CAL_TARGET_EXPOSURE_MS)
        switch_backlight("off", manual_lamp_control=opts.manual_lamp_control)
        switch_fibre_backlight_voltage(0.0, manual_lamp_control=opts.manual_lamp_control)

        # use context manager to switch lamp on
        # and guarantee it is switched off after the
        # measurement (even if exceptions occur)
        with use_ambientlight(manual_lamp_control=opts.manual_lamp_control):
            ipath_selftest_met_cal_target = capture_image(met_cal_cam, "met_cal_target")

    
        met_cal_cam.SetExposureTime(METROLOGY_CAL_FIBRE_EXPOSURE_MS)
        switch_ambientlight("off", manual_lamp_control=opts.manual_lamp_control)
        
        with use_backlight(METROLOGY_CAL_BACKLIGHT_VOLTAGE, manual_lamp_control=opts.manual_lamp_control):
            ipath_selftest_met_cal_fibre = capture_image(met_cal_cam, "met_cal_target")

        target_coordinates = metcalTargetCoordinates(ipath_selftest_met_cal_target, **METCAL_TARGET_ANALYSIS_PARS)
        fibre_coordinates = metcalFibreCoordinates(ipath_selftest_met_cal_fibre, **METCAL_FIBRE_ANALYSIS_PARS)

    finally:
        safe_home_turntable(gd, grid_state)    





def selftest_metrology_height(env, vfdb, gd, grid_state, opts, fpuset, fpu_config, 
                             MET_HEIGHT_POSITIONS=None,
                             MET_HIGHT_TARGET_EXPOSURE_MS=None,
                             MET_HEIGHT_ANALYSIS_PARS=None,
                             capture_image=capture_image):

    try:
        safe_home_turntable(gd, grid_state)    
    
        switch_backlight("off", manual_lamp_control=opts.manual_lamp_control)
        switch_ambientlight("off", manual_lamp_control=opts.manual_lamp_control)
        switch_fibre_backlight_voltage(0.0, manual_lamp_control=opts.manual_lamp_control)
    
        MET_HEIGHT_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                                   IP_ADDRESS : MET_HEIGHT_CAMERA_IP_ADDRESS }
            
        met_height_cam = GigECamera(MET_HEIGHT_CAMERA_CONF)
        
        fpu_id, stage_position  in get_sorted_positions(fpuset, METROLOGY_HEIGHT_POSITIONS)[0]
        # move rotary stage to POS_REP_POSN_N
        turntable_safe_goto(gd, grid_state, stage_position)
            
        with use_silhouettelight(manual_lamp_control=opts.manual_lamp_control):                
            ipath_selftest_met_height = capture_image(met_height_cam)
            
        metht_small_target_height, metht_large_target_height = methtHeight(ipath_selftest_met_height,  **MET_HEIGHT_ANALYSIS_PARS)
    
    finally:
        safe_home_turntable(gd, grid_state)    


        
        
def selftest_positional_repeatability(env, vfdb, gd, grid_state, opts, fpuset, fpu_config,
                                     POSITION_REP_WAVEFORM_PARS=None,
                                     POSITIONAL_REP_ITERATIONS=None,
                                     POSITION_REP_POSITIONS=None,
                                     POSITION_REP_NUMINCREMENTS=None,
                                     POSITIONAL_REP_EXPOSURE_MS=None,
                                     POS_REP_CALIBRATION_PARS=None,
                                     POS_REP_ANALYSIS_PARS=None):

    try:
        safe_home_turntable(gd, grid_state)    

        switch_backlight("off", manual_lamp_control=opts.manual_lamp_control)
        switch_fibre_backlight_voltage(0.0, manual_lamp_control=opts.manual_lamp_control)

        POS_REP_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                                IP_ADDRESS : POS_REP_CAMERA_IP_ADDRESS }
        
        pos_rep_cam = GigECamera(POS_REP_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(POSITIONAL_REP_EXPOSURE_MS)
        
        fpu_id, stage_position = get_sorted_positions(fpuset, POS_REP_POSITIONS)[0]
            
        turntable_safe_goto(gd, grid_state, stage_position)
            
        with use_ambientlight(manual_lamp_control=opts.manual_lamp_control):
                       
            selftest_ipath_pos_rep = capture_image("positional_repeatability")

        coords = posrepCoordinates(selftest_ipath_pos_rep, POSREP_CALIBRATION_PARS=POS_REP_CALIBRATION_PARS, **POS_REP_ANALYSIS_PARS)

    finally:
        safe_home_turntable(gd, grid_state)    
        
        


def selftest(env, vfdb, gd, grid_state, opts, fpuset, fpu_config,
             MET_CAL_MEASUREMENT_PARS=None,
             METCAL_FIBRE_ANALYSIS_PARS=None,
             METCAL_TARGET_ANALYSIS_PARS=None,
             MET_HEIGHT_ANALYSIS_PARS=None,
             MET_HEIGHT_MEASUREMENT_PARS=None,
             POS_REP_ANALYSIS_PARS=None,
             POS_REP_CALIBRATION_PARS=None,
             POS_REP_MEASUREMENT_PARS=None,
             PUPALGN_ANALYSIS_PARS=None,
             PUPALGN_CALIBRATION_PARS=None,
             PUPALGN_MEASUREMENT_PARS=None):

    tstamp=timestamp()


    def capture_image(cam, subtest):
    
        ipath = store_image(cam,
                            "self-test/{ts}/{stest}.bmp",
                            ts=tstamp,
                            stest=subtest)            
        return ipath

    try:
        selftest_pup_algn(env, vfdb, gd, grid_state, opts, fpuset, fpu_config,
                          PUPALGN_ANALYSIS_PARS=PUPALGN_ANALYSIS_PARS,
                          PUPALGN_CALIBRATION_PARS=PUPALGN_CALIBRATION_PARS,
                          **PUPALGN_MEASUREMENT_PARS,
                          capture_image=capture_image)
        
    except exception as e:
        print("pupil alignment self-test failed:", str(e))
        sys.exit(1)
        
    try:        
        selftest_metrology_calibration(env, vfdb, gd, grid_state, opts, fpuset, fpu_config,
                                       METCAL_TARGET_ANALYSIS_PARS=METCAL_TARGET_ANALYSIS_PARS,
                                       METCAL_FIBRE_ANALYSIS_PARS=METCAL_FIBRE_ANALYSIS_PARS,
                                       **MET_CAL_MEASUREMENT_PARS,
                                       capture_image=capture_image):
    except exception as e:
        print("metrology calibration self-test failed", str(e))
        sys.exit(1)


    try:
        selftest_metrology_height(env, vfdb, gd, grid_state, opts, fpuset, fpu_config, 
                                  MET_HEIGHT_ANALYSIS_PARS=None,
                                  **MET_HEIGHT_MEASUREMENT_PARS,
                                  capture_image=capture_image)        
    except exception as e:
        print("metrology height self-test failed", str(e))
        sys.exit(1)



    try:
        selftest_positional_repetability(env, vfdb, gd, grid_state, opts, fpuset, fpu_config, 
                                         POS_REP_ANALYSIS_PARS=POS_REP_ANALYSIS_PARS,
                                         POS_REP_CALIBRATION_PARS=POS_REP_CALIBRATION_PARS,
                                         **POS_REP_MEASUREMENT_PARS,
                                         capture_image=capture_image)        
    except exception as e:
        print("positional repeatability self-test failed", str(e))
        sys.exit(1)
        
