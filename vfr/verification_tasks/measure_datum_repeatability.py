from __future__ import print_function, division

from numpy import NaN

from vfr.conf import POS_REP_CAMERA_IP_ADDRESS 

from vfr.db.datum_repeatability import (TestResult,
                                        save_datum_repeatability_images,
                                        get_datum_repeatability_images, save_datum_repeatability_result,
                                        get_datum_repeatability_result, get_datum_repeatability_passed_p)


from vfr import hw
from vfr import hwsimulation


from GigE.GigECamera import DEVICE_CLASS, BASLER_DEVICE_CLASS, IP_ADDRESS



from fpu_commands import gen_wf


from vfr.tests_common import (timestamp, dirac, goto_position, find_datum, store_image,
                              get_sorted_positions)


from ImageAnalysisFuncs.analyze_positional_repeatability import (posrepCoordinates,
                                                                 evaluate_datum_repeatability,
                                                                 DATUM_REPEATABILITY_ALGORITHM_VERSION)


    

def measure_datum_repeatability(env, vfdb, gd, grid_state, opts, fpuset, fpu_config,
                                DATUM_REP_POSITIONS=None,
                                DATUM_REP_ITERATIONS=None,
                                DATUM_REP_PASS=None,
                                DATUM_REP_EXPOSURE_MS=None):

    tstamp=timestamp()
    if opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    # home turntable
    hw.safe_home_turntable(gd, grid_state)    

    hw.switch_backlight("off", manual_lamp_control=opts.manual_lamp_control)
    hw.switch_fibre_backlight_voltage(0.0, manual_lamp_control=opts.manual_lamp_control)

    with hw.use_ambientlight(manual_lamp_control=opts.manual_lamp_control):
    
        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position  in get_sorted_positions(fpuset, DATUM_REP_POSITIONS):
    
            if (get_datum_repeatability_passed_p(env, vfdb, opts, fpu_config, fpu_id) and (
                    not opts.repeat_passed_tests)):
    
                sn = fpu_config[fpu_id]['serialnumber']
                print("FPU %s : datum repeatability test already passed, skipping test" % sn)
                continue

            
            # move rotary stage to POS_REP_POSN_N
            hw.turntable_safe_goto(gd, grid_state, stage_position)            
        
            # initialize pos_rep camera
            # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
            MET_CAL_CAMERA_CONF = { DEVICE_CLASS : BASLER_DEVICE_CLASS,
                                    IP_ADDRESS : MET_CAL_CAMERA_IP_ADDRESS }
            
            met_cal_cam = hw.GigECamera(MET_CAL_CAMERA_CONF)
            met_cal_cam.SetExposureTime(DATUM_REP_EXPOSURE_MS)
            
    
            datumed_images = []
            moved_images = []
    
            def capture_image(subtest, count):
    
                ipath = store_image(pos_rep_cam,
                                    "{sn}/{tn}/{ts}/{tp}-{tc:02d}-{ic:03d}-.bmp",
                                    sn=fpu_config[fpu_id]['serialnumber'],
                                    tn="datum-repeatability",
                                    ts=ttamp,
                                    tp=testphase,
                                    tc=testcount,
                                    ic=count)
                
                return ipath
    
                
        
            for k in range(DATUM_REP_ITERATIONS):
                gd.findDatum(grid_state, fpuset=[fpu_id])
                ipath = capture_image("datumed", count)
                datumed_images.append(ipath)
        
            gd.findDatum(grid_state)
            for k in range(DATUM_REP_ITERATIONS):
                wf = gen_wf(30 * dirac(fpu_id), 30)
                gd.configMottion(wf, grid_state)
                gd.executeMotion(grid_state, fpuset=[fpu_id])
                gd.reverseMotion(grid_state, fpuset=[fpu_id])
                gd.executeMotion(grid_state, fpuset=[fpu_id])
                gd.findDatum(grid_state, fpuset=[fpu_id])
                ipath, coords = capture_image("moved+datumed", count)
                moved_images.append(ipath)
    
            images = { 'datumed_images' : datumed_images,
                       'moved_images' : moved_images }
            
    
            save_datum_repeatability_images(env, vfdb, opts, fpu_config, fpu_id, images)
    


def eval_datum_repeatability(env, vfdb, gd, grid_state, opts, fpuset, fpu_config, pos_rep_analysis_pars):

    for fpu_id in fpuset:
        images = get_datum_repeatability_images(env, vfdb, opts, fpu_config, fpu_id, images)

        def analysis_func(ipath):
            return posrepCoordinates(ipath, **pos_rep_analysis_pars)
        

        try:
            
            datumed_coords = map(analysis_func, images['datumed_images'])
            moved_coords = map(analysis_func, images['moved_images'])
        

            datum_repeatability_mm = evaluate_datum_repeatability(datumed_coords, moved_coords)

            datum_repeatability_has_passed = TestResult.OK if datum_repeatability_mm <= DATUM_REP_PASS else TestResult.FAILED
        
            coords = { 'datumed_coords' : datumed_coords,
                       'moved_coords' : moved_coords }
            errmsg = ""
            
        except ImageAnalysisError as e:
            errmsg = str(e)
            coords = {}
            datum_repeatability_mm = NaN
            datum_repeatability_has_passed = TestResult.NA
            

        save_datum_repeatability_result(env, vfdb, opts, fpu_config, fpu_id, coords=coords,
                                        datum_repeatability_mm=datum_repeatability_mm,
                                        datum_repeatability_has_passed=datum_repeatability_has_passed,
                                        ermmsg=errmsg,
                                        analysis_version=DATUM_REPEATABILITY_ALGORITHM_VERSION)
        



