from __future__ import print_function, division


from numpy import NaN

from GigE.GigECamera import DEVICE_CLASS, BASLER_DEVICE_CLASS, IP_ADDRESS
from vfr.conf import POS_REP_CAMERA_IP_ADDRESS

from vfr.verification_tasks.measure_datum_repeatability import get_datum_repeatability_passed_p
from vfr.db.positional_repeatability import (TestResult,
                                             save_positional_repeatability_images,
                                             get_positional_repeatability_images,
                                             save_positional_repeatability_result,
                                             get_positional_repeatability_result,
                                             get_positional_repeatability_passed_p)

from vfr import hw
from vfr import hwsimulation


from fpu_commands import gen_wf


from vfr.tests_common import (flush, timestamp, dirac, goto_position, find_datum, store_image,
                              get_sorted_positionse)


from ImageAnalysisFuncs.analyze_positional_repeatability import (posrepCoordinates,
                                                                 evaluate_positional_repeatability, 
                                                                 POSITIONAL_REPEATABILITY_ALGORITHM_VERSION, fit_gearbox_correction)


from Gearbox.gear_correction import GearboxFitError, fit_gearbox_correction


    
def measure_positional_repeatability(env, vfdb, gd, grid_state, opts, fpuset, fpu_config,
                                     POSITION_REP_WAVEFORM_PARS=None,
                                     POSITIONAL_REP_ITERATIONS=None,
                                     POSITION_REP_POSITIONS=None,
                                     POSITION_REP_NUMINCREMENTS=None,
                                     POSITIONAL_REP_EXPOSURE_MS=None):

    tstamp=timestamp()
    if opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    # home turntable
    hw.safe_home_turntable(gd, grid_state)    

    hw.switch_backlight("off", manual_lamp_control=opts.manual_lamp_control)
    hw.switch_fibre_backlight_voltage(0.0, manual_lamp_control=opts.manual_lamp_control)

    with use_ambientlight(manual_lamp_control=opts.manual_lamp_control):
        # initialize pos_rep camera
        # set pos_rep camera exposure time to POSITIONAL_REP_EXPOSURE milliseconds
        POS_REP_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                                IP_ADDRESS : POS_REP_CAMERA_IP_ADDRESS }
        
        pos_rep_cam = hw.GigECamera(POS_REP_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(POSITIONAL_REP_EXPOSURE_MS)
        
        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position  in get_sorted_positions(fpuset, POS_REP_POSITIONS):
            
            if not get_datum_repeatability_passed_p(env, vfdb, opts, fpu_config, fpu_id):
                print("FPU %s: skipping positional repeatability measurement because"
                      " there is no passed datum repeatability test" % fpu_config['serialnumber'])
                continue
    
            if not get_pupil_alignment_passed_p(env, vfdb, opts, fpu_config, fpu_id):
                print("FPU %s: skipping positional repeatability measurement because"
                      " there is no passed pupil alignment test" % fpu_config['serialnumber'])
                continue
    
            if (get_positional_repeatability_passed_p(env, vfdb, opts, fpu_config, fpu_id) and (
                    not opts.repeat_passed_tests)):
    
                sn = fpu_config[fpu_id]['serialnumber']
                print("FPU %s : positional repeatability test already passed, skipping test" % sn)
                continue
    
            
            # move rotary stage to POS_REP_POSN_N
            hw.turntable_safe_goto(gd, grid_state, stage_position)            
                
    
            image_dict = {}
    
            def capture_image(iteration, increment, direction, alpha, beta):
    
                ipath = store_image(pos_rep_cam,
                                    "{sn}/{tn}/{ts}/{itr:03d}-{inc:03d}-{dir:03d}-{alpha:+08.3f}-{beta:+08.3f}.bmp",
                                    sn=fpu_config[fpu_id]['serialnumber'],
                                    tn="positional-repeatability",
                                    ts=tstamp,
                                    itr=iteration,
                                    inc=increment,
                                    dir=direction)
                
                return ipath
    
                
            
            
            for i in range(POSITIONAL_REP_ITERATIONS):
                gd.findDatum(grid_state, fpuset=[fpu_id])
                
                step_a = 320.0 / POSITIONAL_REP_INCREMENTS
                step_b = 320.0 / POSITIONAL_REP_INCREMENTS

                alpha0 = -170.0
                beta0 = -170.0
                    
    
                for j in range(4):

                    M = POSITIONAL_REP_INCREMENTS
                    for k in range(M):
                        if j == 0:
                            ka = k
                            kb = 0
                        elif j == 1:
                            ka = M - k - 1
                            kb = 0
                        elif j == 2:
                            ka = 0
                            kb = l
                        elif j == 3:
                            ka = 0
                            kb = M - k - 1
                            
                            
                        abs_alpha = alpha0 + step_a * ka
                        abs_beta = beta0 + step_b * kb
                        goto_position(gd, abs_alpha, abs_beta, grid_state, fpuset=[fpu_id])
                            
                        angles = gd.countedAngles()
                        alpha_count = angles[fpu_id][0]
                        beta_count = angles[fpu_id][1]
                        alpha_steps = grid_state.FPU[fpu_id].alpha_steps
                        beta_steps = grid_state.FPU[fpu_id].beta_steps
                        
                        ipath = capture_image(i, j, k, alpha_count, beta_count)
                        image_dict[(abs_alpha, abs_beta, i, j, k)] = (alpha_steps, beta_steps, ipath)
                        
    
                            
                        
        
            
    
            save_positional_repeatability_images(env, vfdb, opts, fpu_config, fpu_id, image_dict,
                                                 waveform_pars=POSITION_REP_WAVEFORM_PARS)
    


def eval_positional_repeatability(env, vfdb, gd, grid_state, opts, fpuset, fpu_config,
                                  pos_rep_calibration_pars,
                                  pos_rep_analysis_pars,
                                  pos_rep_evaluation_pars):

    def analysis_func(ipath):
        return posrepCoordinates(ipath, POSREP_CALIBRATION_PARS=pos_rep_calibration_pars, **pos_rep_analysis_pars)

    
    for fpu_id in fpuset:
        images = get_positional_repeatability_images(env, vfdb, opts, fpu_config, fpu_id, images)

        
        try:
            analysis_results = {}
            
            for k, v in images.items():
                alpha_steps, beta_steps, ipath = v
                (x_measured_small, y_measured_small, qual_small, x_measured_big, y_measured_big, qual_big) = analysis_func(ipath)
                
                analysis_results[k] = (x_measured_small, y_measured_small,
                                       x_measured_big, y_measured_big)
                                 
        
        
            positional_repeatability_mm = evaluate_positional_repeatability(analysis_results, **pos_rep_evaluation_pars)

            positional_repeatability_has_passed = positional_repeatability_mm <= POSITIONAL_REP_PASS

            gearbox_correction = fit_gearbox_correction(analysis_results)
        

        except (ImageAnalysisError, GearboxFitError) as e:
            analysis_results = None
            errmsg = str(e)
            positional_repeatability_mm = NaN
            positional_repeatability_has_passed = TestResult.NA
            

        save_positional_repeatability_result(env, vfdb, opts, fpu_config, fpu_id,
                                             pos_rep_calibration_pars=pos_rep_calibration_pars,
                                             analysis_results=analysis_results,
                                             positional_repeatability_mm=positional_repeatability_mm, 
                                             positional_repeatability_has_passed=positional_repetability_has_passed,
                                             gearbox_correction=gearbox_correction,
                                             ermmsg=errmsg,
                                             analysis_version=POSITIONAL_REPEATABILITY_ALGORITHM_VERSION)
        
        



