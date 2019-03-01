from __future__ import print_function, division

import os
from os import path
from numpy import zeros, nan
from protectiondb import ProtectionDB as pdb
from vfr.conf import PUP_ALN_CAMERA_IP_ADDRESS, NR360_SERIALNUMBER

from vfr.db import (env,
                    TestResult,
                    save_pupil_alignment_images,
                    get_pupil_alignment_images,
                    save_pupil_alignment_result,
                    get_pupil_alignment_result)

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

from Lamps.lctrl import switch_backlight, switch_ambientlight

import pyAPT

from ImageAnalysisFuncs.analyze_pupil_alignment import (pupil_alignment_image_analysis, 
                                                        evaluate_pupil_alignment,
                                                        PUPIL_ALIGNMENT_ALGORITHM_VERSION)




def generate_positions():
    a0 = -170.0
    b0 = -170.0
    delta_a = 90.0
    delta_b = 90.0
    for j in range(4):
        for k in range(4):
            yield (a0 + delta_a * j , b0 + delta_b * k)
    a_near = 1.0
    b_near = 1.0
    
    yield (ALPHA_DATUM_OFFSET + a_near, 0 + b_near)

def measure_pupil_alignment(env, vfdb, gd, grid_state, args, fpuset, fpu_config,
                            PUPIL_ALN_POSITIONS=None,
                            PUPIL_ALN_LINPOSITIONS=None,
                            PUPIL_ALN_EXPOSURE_MS=None):

    tstamp=timestamp()

    # home turntable
    safe_home_turntable(gd, grid_state)    
    home_linear_stage()    

    switch_ambientlight("off", manual_lamp_control=args.manual_lamp_control)
    switch_silhouettelight("off", manual_lamp_control=args.manual_lamp_control)
    switch_fibre_backlight_voltage(5.0, manual_lamp_control=args.manual_lamp_control)
    switch_backlight("on", manual_lamp_control=args.manual_lamp_control)

    # initialize pos_rep camera
    # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
    PUP_ALN_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                            IP_ADDRESS : PUP_ALN_CAMERA_IP_ADDRESS }
        
    pup_aln_cam = GigECamera(PUP_ALN_CAMERA_CONF)
    pup_aln_cam.SetExposureTime(PUPIL_ALN_EXPOSURE_MS)
        
    # get sorted positions (this is needed because the turntable can only
    # move into one direction)
    for fpu_id, stage_position  in get_sorted_positions(fpuset, PUP_ALN_POSITIONS):
        # move rotary stage to PUP_ALN_POSN_N
        turntable_safe_goto(gd, grid_state, stage_position)            
        linear_stage__goto(PUPIL_ALN_LINPOSITIONS[fpu_id])            
    
        

        unmoved_images = []
        datumed_images = []
        moved_images = []

        def capture_image(count, alpha, beta):

            ipath = store_image(pup_aln_cam,
                                "{sn}/{tn}/{ts}/{tp}-{cnt:02d}-{alpha:+08.3f}-{beta:+08.3f}.bmp",
                                sn=fpu_config[fpu_id]['serialnumber'],
                                tn="pupil-alignment",
                                ts=tstamp,
                                cnt=count,
                                alpha=alpha,
                                beta=beta)
            
            return ipath


        images = {}
        for count, coords in enumerate(generate_positions()):
            abs_alpha, abs_beta = coords
            goto_position(gd, abs_alpha, abs_beta, grid_state, fpuset=[fpu_id])
            
            if count < 16:
                ipath = capture_image(count, alpha, beta)
                images[(alpha, beta)] = ipath

        gd.findDatum(grid_state, fpuset=[fpu_id])

        save_pupil_alignment_images(env, vfdb, args, fpu_config, fpu_id, images)



def eval_pupil_alignment(env, vfdb, gd, grid_state, args, fpuset, fpu_config,
                         PUPALGN_CALIBRATION_PARS=None,
                         PUPALGN_ANALYSIS_PARS=None, PUPIL_ALN_PASS=NaN):

    for fpu_id in fpuset:
        images = get_pupil_alignment_images(env, vfdb, args, fpu_config, fpu_id, images)

        def analysis_func(ipath):
            return pupil_alignment_image_analysis(ipath, PUPALGN_CALIBRATION_PARS, **PUPALGN_ANALYSIS_PARS)
        

        try:
            coords = dict( (k, analysis_func(v)) for k, v in images.items() )
                    

            pupalnChassisErr, pupalnAlphaErr, pupalnBetaErr,  pupalnTotalErr = evaluate_pupil_alignment(coords)

            pupil_alignment_has_passed = TestResult.OK if pupil_alignment_mm <= PUPIL_ALN_PASS else TestResult.FAILED
        
            errmsg = ""
            
        except ImageAnalysisError as e:
            errmsg = str(e)
            coords = {}
            pupalnChassisErr = pupalnAlphaErr = pupalnBetaErr =  pupalnTotalErr = NaN
            pupil_alignment_has_passed = TestResult.NA
            

        pupil_alignment_measures = { 'chassis_error':  pupalnChassisErr,
                                      'alpha_error' : pupalnAlphaErr,
                                      'beta_error' : pupalnBetaErr,
                                      'total_error' :pupalnTotalErr}
        
        save_pupil_alignment_result(env, vfdb, args, fpu_config, fpu_id,
                                    calibration_pars=PUPALGN_CALIBRATION_PARS,
                                    coords=coords,
                                    pupil_alignment_measures=pupil_alignment_measures,
                                    pupil_alignment_has_passed=datum_repetability_has_passed,
                                    ermmsg=errmsg,
                                    analysis_version=PUPIL_ALIGNMENT_ALGORITHM_VERSION)
        



