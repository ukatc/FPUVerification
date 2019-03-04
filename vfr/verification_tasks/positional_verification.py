from __future__ import print_function, division

import os
from os import path
from numpy import zeros, nan
from protectiondb import ProtectionDB as pdb
from GigE.GigECamera import DEVICE_CLASS, BASLER_DEVICE_CLASS, IP_ADDRESS
from vfr.conf import POS_REP_POSN_N, POS_REP_CAMERA_IP_ADDRESS, NR360_SERIALNUMBER

from vfr.verification_tasks.measure_datum_repeatability import get_datum_repeatability_passed_p

from vfr.verification_tasks.positional_repeatability import (get_positional_repeatability_result,
                                                             get_positional_repeatability_passed_p )

from vfr.db.positional_verification import (env,
                                            TestResult,
                                            save_positional_verification_images,
                                            get_positional_verification_images,
                                            save_positional_verification_result)
                                            
                                           
from vfr import turntable

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
                                                                 evaluate_positional_verification, 
                                                                 POSITIONAL_VERIFICATION_ALGORITHM_VERSION, fit_gearbox_correction)

from Gearbox.gear_correction import GearboxFitError, apply_gearbox_correction

    


def generate_tested_positions(niterations):
    positions = []
    ALPHA_MIN = -179.0
    ALPHA_MAX = +150.0
    BETA_MIN = -175.0
    BETA_MAX = +150.0
    
    for k in range(8):
        positions.append((10.0 + k * 45.0, -170.0))
    for r in range(niterations):
        alpha = random.uniform(ALPHA_MIN, ALPHA_MAX)
        beta = random.uniform(BETA_MIN, BETA_MAX)
        positions.append( (alpha, beta))

    return positions
    
def measure_positional_verification(env, vfdb, gd, grid_state, args, fpuset, fpu_config, 
                                     POSITIONAL_VER_ITERATIONS=None,
                                     POSITION_REP_POSITIONS=None,
                                     POSITIONAL_VER_EXPOSURE_MS=None):

    # home turntable
    tstamp=timestamp()
    
    safe_home_turntable(gd, grid_state)    

    switch_backlight("off", manual_lamp_control=args.manual_lamp_control)
    switch_ambientlight("on", manual_lamp_control=args.manual_lamp_control)
    switch_fibre_backlight_voltage(0.0, manual_lamp_control=args.manual_lamp_control)

    # initialize pos_rep camera
    # set pos_rep camera exposure time to POSITIONAL_VER_EXPOSURE milliseconds
    POS_VER_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                            IP_ADDRESS : POS_REP_CAMERA_IP_ADDRESS }
    
    pos_rep_cam = GigECamera(POS_VER_CAMERA_CONF)
    pos_rep_cam.SetExposureTime(POSITIONAL_VER_EXPOSURE_MS)

    
    # get sorted positions (this is needed because the turntable can only
    # move into one direction)
    for fpu_id, stage_position  in get_sorted_positions(fpuset, POS_REP_POSITIONS):
        
        if not get_datum_verification_passed_p(env, vfdb, args, fpu_config, fpu_id):
            print("FPU %s: skipping positional verification measurement because"
                  " there is no passed datum verification test" % fpu_config['serialnumber'])
            continue

        if not get_pupil_alignment_passed_p(env, vfdb, args, fpu_config, fpu_id):
            print("FPU %s: skipping positional verification measurement because"
                  " there is no passed pupil alignment test" % fpu_config['serialnumber'])
            continue

        if not get_positional_repeatability_passed_p(env, vfdb, args, fpu_config, fpu_id):
            print("FPU %s: skipping positional verification measurement because"
                  " there is no passed positional repetability test" % fpu_config['serialnumber'])
            continue

        if (get_datum_verification_passed_p(env, vfdb, args, fpu_config, fpu_id) and (
                not args.repeat_passed_tests)):

            sn = fpu_config[fpu_id]['serialnumber']
            print("FPU %s : datum verification test already passed, skipping test" % sn)
            continue
        
        pr_result = get_positional_repeatability_result(env, vfdb, args, fpu_config, fpu_id)
        gearbox_correction = pr_result['gearbox_correction']
        fpu_coeffs = gearbox_correction['coeffs']
        
        # move rotary stage to POS_VER_POSN_N
        turntable_safe_goto(gd, grid_state, stage_position)            
            

        image_dict = {}


        def capture_image(idx, alpha, beta):

            ipath = store_image(pos_rep_cam,
                                "{sn}/{tn}/{ts}/{idx:04d}-{alpha:+08.3f}-{beta:+08.3f}.bmp",
                                sn=fpu_config[fpu_id]['serialnumber'],
                                tn="positional-verification",
                                alpha=alpha,
                                beta=beta,
                                ts=tstamp,
                                idx=dx)
            
            return ipath

            
        
        tested_positions = generate_tested_positions(POSITIONAL_VER_ITERATIONS)
        
        gd.findDatum(grid_state, fpuset=[fpu_id])

        image_dict = {}
        for k, (alpha, beta) in enumerate(tested_positions):
            # get current step count
            alpha_cursteps = grid_state.FPU[fpu_id].alpha_steps
            beta_cursteps = grid_state.FPU[fpu_id].beta_steps

            # get absolute corrected step count from desired absolute angle
            asteps_target, bsteps_target = apply_gearbox_correction((alpha, beta), coeffs=fpu_coeffs)

            # compute deltas of step counts
            adelta = asteps_target - alpha_cursteps
            bdelta = bsteps_target - beta_cursteps

            # move by delta
            wf = gen_wf(dirac(fpu_id) * adelta, dirac(fpu_id) * bdelta, units='steps')
            
            gd.configMotion(wf, grid_state)
            gd.executeMotion(grid_state)

            ipath = capture_image(k, alpha, beta)

            image_dict[(k, alpha, beta)] = ipath

        # store dict of image paths
        save_positional_verification_images(env, vfdb, args, fpu_config, fpu_id, image_dict)



def eval_positional_verification(env, vfdb, gd, grid_state, args, fpuset, fpu_config,
                                  pos_rep_analysis_pars, pos_ver_evaluation_pars):

    def analysis_func(ipath):
        return positional_repeatability_image_analysis(ipath, **pos_rep_analysis_pars)

    
    for fpu_id in fpuset:
        image_dict = get_positional_verification_images(env, vfdb, args, fpu_config, fpu_id)

        
        try:
            analysis_results = {}
            
            for k, v in images.items():
                alpha = k[1]
                beta = k[2]
                (x_measured_1, y_measured_1, qual1, x_measured_2, y_measured_2, qual2) = analysis_func(v)
                analysis_results[k] = (x_measured_1, y_measured_1, x_measured_2, y_measured_2)
                                 
        
        
            posver_errors, positional_verification_mm = evaluate_positional_verification(analysis_results, **pos_ver_evaluation_pars)

            positional_verification_has_passed = TestResult.OK if positional_verification_mm <= POSITIONAL_VER_PASS else TestResult.FAILED
        

        except ImageAnalysisError as e:
            analysis_results = None
            errmsg = str(e)
            posver_errors = None
            positional_verification_mm = NaN
            positional_verification_has_passed = TestResult.NA
            

        save_positional_verification_result(env, vfdb, args, fpu_config, fpu_id, analysis_results=analysis_results,
                                            posver_errors=posver_errors,
                                            positional_verification_mm=positional_verification_mm, 
                                            positional_verification_has_passed=positional_verification_has_passed,
                                            ermmsg=errmsg,
                                            analysis_version=POSITIONAL_VERIFICATION_ALGORITHM_VERSION)
        
        



