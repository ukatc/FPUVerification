from __future__ import print_function, division

import os
from os import path

from vfr.db.datum import (get_datum_result, get_datum_passed_p)

from vfr.db.colldect_limits import (get_angular_limit,
                                    get_anglimit_passed_p,
                                    get_colldect_passed_p)

from vfr.db.datum_repeatability import (get_datum_repeatability_images, 
                                        get_datum_repeatability_result,
                                        get_datum_repeatability_passed_p)

from vfr.db.metrology_calibration import (get_metrology_calibration_images,
                                          get_metrology_calibration_result)

from vfr.db.metrology_height import (get_metrology_height_images,
                                     get_metrology_height_result)

from vfr.db.positional_repeatability import (get_positional_repeatability_images,
                                            get_positional_repeatability_result,
                                            get_positional_repeatability_passed_p)

from vfr.db.positional_verification import (get_positional_verification_images,
                                            get_positional_verification_result)

from vfr.db.pupil_alignment import (get_pupil_alignment_images,
                                    get_pupil_alignment_result,
                                    get_pupil_alignment_passed_p)

def get_data(env, vfdb, gd, grid_state, opts, fpu_id, fpu_config):
    serial_number = fpu_config[fpu_id]['serialnumber']
    datum_result = get_datum_result(env, vfdb, opts, fpu_config, fpu_id)

    alpha_min_result = get_angular_limit(env, vfdb, fpu_id, serialnumber, "alpha_min")
    alpha_max_result = get_angular_limit(env, vfdb, fpu_id, serialnumber, "alpha_max")
    beta_min_result = get_angular_limit(env, vfdb, fpu_id, serialnumber, "beta_min")
    beta_max_result = get_angular_limit(env, vfdb, fpu_id, serialnumber, "beta_max")        
    beta_collision_result = get_angular_limit(env, vfdb, fpu_id, serialnumber, "beta_collision")
    
    datum_repeatability_result = get_datum_repeatability_result(env, vfdb, fpu_id, serialnumber)
    metrology_calibration_result = get_metrology_calibration_result(env, vfdb, fpu_id, serialnumber)

    metrology_height_result = get_metrology_height_result(env, vfdb, opts, fpu_config, fpu_id)
    positional_repeatability_result = get_positional_repeatability_result(env, vfdb, opts, fpu_config, fpu_id)
    positional_verification_result = get_positional_verification_result(env, vfdb, opts, fpu_config, fpu_id)
    pupil_alignment_result = get_pupil_alignment_result(env, vfdb, opts, fpu_config, fpu_id)
    
        
    outfile = opts.output_file

    return locals()

        
def print_report_terse(serial_number=None,
                       datum_result=None,
                       alpha_min_result=None,
                       alpha_max_result=None,
                       beta_min_result=None,
                       beta_max_result=None,
                       beta_collision_result=None,
                       datum_repeatability_result=None,
                       metrology_calibration_result=None,
                       metrology_height_result=None,
                       positional_repeatability_result=None,
                       positional_verification_result=None,
                       pupil_alignment_result=None,
                       outfile=None):

    print("*" * 60, file=outfile)
    print("FPU %s" % serial_number, file=outfile)

    if datum_result is None:
        print("Datum test: n/a", file=outfile)
    else:
        print("Datum test: alpha datumed = %s" % datum_result['datumed'][0], file=outfile) 
        print("Datum test: beta datumed = %s" % datum_result['datumed'][1], file=outfile)
        print("Datum test: result = %s" % datum_result['diagnostic'], file=outfile)


    if beta_collision_result is None:
        print("Beta collision  test: n/a", file=outfile)
    else:
        print("Collision detection: result = %s (%s)" % (beta_collision_result['result'],
                                                         beta_collision_result['diagnostic']), file=outfile)

    
    if alpha_min_result is None:
        print("Limit test:  alpha min n/a", file=outfile)
    else:
        print("Limit test: alpha min = %s limit = %6.2f (%s)" % (alpha_min_result['result'],
                                                                 alpha_min_result['val']
                                                                 alpha_min_result['diagnostic']), file=outfile)
    if alpha_max_result is None:
        print("Limit test:  alpha max n/a", file=outfile)
    else:
        print("Limit test: alpha max = %s limit = %6.2f (%s)" % (alpha_max_result['result'],
                                                                 alpha_max_result['val'],
                                                                 alpha_max_result['diagnostic']), file=outfile)
    
    if beta_min_result is None:
        print("Limit test: beta min n/a", file=outfile)
    else:
        print("Limit test: beta min = %s limit = %6.2f (%s)" % (beta_min_result['result'],
                                                                beta_min_result['val']
                                                                beta_min_result['diagnostic']), file=outfile)
    if beta_max_result is None:
        print("Limit test: beta max n/a", file=outfile)
    else:
        print("Limit test: beta max = %s limit = %6.2f (%s)" % (beta_max_result['result'],
                                                                beta_max_result['val'],
                                                                beta_max_result['diagnostic']), file=outfile)

    if datum_repeatability_result is None:
        print("Datum repeatability: n/a", file=outfile)
    else:
        err_msg = datum_repeatability_result['error_message']
        if len(err_msg) == 0:
            print("Datum repeatability: %s, delta = %6.2" %(datum_repeatability_result['result'],
                                                            datum_repeatability_result['repeatability_millimeter']), file=outfile)
        else:
            print("Datum repeatability: %s" % err_msg, file=outfile)

    if metrology_calibration_result is None:
        print("metrology calibration: n/a", file=outfile)
    else:
        err_msg = metrology_calibration_result['error_message']
        if len(err_msg) == 0:
            print("Metrology calibration: fibre_distance = %6.2" % metrology_calibration_result['fibre_distance']), file=outfile)
        else:
            print("Metrology calibration: fibre_distance = %s" % err_msg, file=outfile)

            
    if metrology_height_result is None:
        print("metrology_height: n/a", file=outfile)
    else:
        err_msg = metrology_height_result['error_message']
        if len(err_msg) == 0:
            print("Metrology height: small target = %6.2, large target = %6.2" % (
                metrology_height_result['small_target_height'],
                metrology_height_result['large_target_height']), file=outfile)
        else:
            print("Metrology calibration: fibre_distance = %s" % err_msg, file=outfile)

        
    if positional_repeatability_result is None:
        print("positional repeatability: n/a", file=outfile)
    else:
        err_msg = positional_repeatability_result['error_message']
        if len(err_msg) == 0:
            print("positional repeatability: passed = %s = %6.2f" % (
                positional_repeatability_result['result'],
                positional_repeatability_result['repeatability_millimeter']), file=outfile)
        else:
            print("Positional repeatability: message = %s" % err_msg, file=outfile)

    if positional_verification_result is None:
        print("positional verification: n/a", file=outfile)
    else:
        err_msg = positional_verification_result['error_message']
        if len(err_msg) == 0:
            print("positional verification: passed = %s = %6.2f" % (
                positional_verification_result['result'],
                positional_verification_result['verification_millimeter']), file=outfile)
        else:
            print("Positional verification: message = %s" % err_msg, file=outfile)

    if pupil_alignment_result is None:
        print("pupil_alignment test: n/a", file=outfile)
    else:
        err_msg = pupil_alignment_result['error_message']
        if len(err_msg) == 0:
            print("pupil alignment: passed = %s = %6.2f" % (
                pupil_alignment_result['result'],
                pupil_alignment_result['measures']), file=outfile)
        else:
            print("pupil alignment: message = %s" % err_msg, file=outfile)

        
def print_report_long(serial_number=None,
                       datum_result=None,
                       alpha_min_result=None,
                       alpha_max_result=None,
                       beta_min_result=None,
                       beta_max_result=None,
                       beta_collision_result=None,
                       datum_repeatability_result=None,
                       metrology_calibration_result=None,
                       metrology_height_result=None,
                       positional_repeatability_result=None,
                       positional_verification_result=None,
                       pupil_alignment_result=None,
                       outfile=None):

    print("*" * 60, file=outfile)
    print("FPU %s" % serial_number, file=outfile)
    if datum_result is None:
        print("Datum test: n/a", file=outfile)
    else:
        print("Datum test: alpha datumed = %s" % datum_result['datumed'][0], file=outfile) 
        print("Datum test: beta datumed = %s" % datum_result['datumed'][1], file=outfile)
        print("Datum test: fpu_id/FPU state = %s / %s" % (datum_result['fpu_id'], datum_result['result_state']), file=outfile)
        print("Datum test: counter deviations = %r" % datum_result['counter_deviation'], file=outfile)
        print("Datum test: time = %s" % datum_result['time'], file=outfile)
        print("Datum test: result = %s" % datum_result['diagnostic'], file=outfile)
    
    if beta_collision_result is None:
        print("Beta collision  test: n/a", file=outfile)
    else:
        print("Collision detection: result = %s (%s), time = %s" % (beta_collision_result['result'],
                                                         beta_collision_result['diagnostic']), file=outfile)
        
    if alpha_min_result is None:
        print("Limit test:  alpha min n/a", file=outfile)
    else:
        print("Limit test: alpha min = %s, limit = %7.2f (%s), time = %s" % (alpha_min_result['result'],
                                                                            alpha_min_result['val'],
                                                                            alpha_min_result['diagnostic'],
                                                                            alpha_min_result['time']), file=outfile)
    if alpha_max_result is None:
        print("Limit test:  alpha max n/a", file=outfile)
    else:
        print("Limit test: alpha max = %s, limit = %7.2f (%s), time = %s" % (alpha_max_result['result'],
                                                                 alpha_max_result['val'],
                                                                 alpha_max_result['diagnostic'],
                                                                 alpha_max_result['time']), file=outfile)
    
    if beta_min_result is None:
        print("Limit test: beta min n/a", file=outfile)
    else:
        print("Limit test: beta min = %s, limit = %7.2f (%s), time = %s" % (beta_min_result['result'],
                                                                            beta_min_result['val'],
                                                                            beta_min_result['diagnostic'],
                                                                            beta_min_result['time']), file=outfile)
    
    if beta_max_result is None:
        print("Limit test: beta max n/a", file=outfile)
    else:
        print("Limit test: beta max = %s, limit = %7.2f (%s), time = %s" % (beta_max_result['result'],
                                                                            beta_max_result['val'],
                                                                            beta_max_result['diagnostic'],
                                                                            beta_max_result['time']), file=outfile)

    if datum_repeatability_result is None:
        print("Datum repeatability: n/a", file=outfile)
    else:
        err_msg = datum_repeatability_result['error_message']
        if len(err_msg) == 0:
            print("Datum repeatability: %s, delta = %7.2 mm, time = %s, version = %s" %
                  (datum_repeatability_result['result'],
                   datum_repeatability_result['repeatability_millimeter'],
                   datum_repeatability_result['time'],
                   datum_repeatability_result['algorithm_version']), file=outfile)
            
            print("Datum repeatability: coords = %r" % (err_msg, datum_repeatability_result['coords']), file=outfile)
        else:
            print("Datum repeatability: %s, time = %s, version = %s" %
                  (err_msg,
                   datum_repeatability_result['time'],
                   datum_repeatability_result['algorithm_version']), file=outfile)

    if metrology_calibration_result is None:
        print("metrology calibration: n/a", file=outfile)
    else:
        err_msg = metrology_calibration_result['error_message']
        if len(err_msg) == 0:
            print("Metrology calibration: fibre_distance = %7.2 mm, time=%s, version = %s" %
                  (metrology_calibration_result['fibre_distance'],
                   metrology_calibration_result['time'],
                   metrology_calibration_result['algorithm_version']), file=outfile)
        else:
            print("Metrology calibration: fibre_distance = %s, time = %s, version = %s" % (
                err_msg,
                metrology_calibration_result['time'],
                metrology_calibration_result['algorithm_version']) file=outfile)
    
    if metrology_height_result is None:
        print("metrology_height: n/a", file=outfile)
    else:
        err_msg = metrology_height_result['error_message']
        if len(err_msg) == 0:
            print("Metrology height: small target = %6.2, large target = %6.2, time = %s, version = %s" % (
                metrology_height_result['small_target_height'],
                metrology_height_result['large_target_height'],
                metrology_height_result['time'],
                metrology_height_result['algorithm_version']), file=outfile)
        else:
            print("Metrology calibration: fibre_distance = %s, time = %s, version = %s" %
                  (err_msg,
                   metrology_height_result['time'],
                   metrology_height_result['algorithm_version']) file=outfile)
    
        
    if positional_repeatability_result is None:
        print("positional repeatability: n/a", file=outfile)
    else:
        err_msg = positional_repeatability_result['error_message']
        if len(err_msg) == 0:
            print("positional repeatability: passed = %s,  repetability = %6.2f mm, time = %s, version = %s" % (
                positional_repeatability_result['result'],
                positional_repeatability_result['repeatability_millimeter'],
                positional_repeatability_result['time'],
                positional_repeatability_result['algorithm_version']), file=outfile)
            
            print("Positional repeatability: calibration_pars = %r" % 
                  positional_repeatability_result['calibration_pars'], file=outfile)
            
            print("Positional repeatability: analysis_results = %r" % 
                  positional_repeatability_result['analysis_results'], file=outfile)
            
            print("Positional repeatability: gearbox_correction = %r" % 
                  positional_repeatability_result['gearbox_correction'], file=outfile)
        else:
            print("Positional repeatability: message = %s, time = %s, version = %s" % (err_msg,
                positional_repeatability_result['time'],
                positional_repeatability_result['algorithm_version']), file=outfile)
    

    if positional_verification_result is None:
        print("positional verification: n/a", file=outfile)
    else:
        err_msg = positional_verification_result['error_message']
        if len(err_msg) == 0:
            print("positional verification: passed = %s,  verification_delta = %6.2f mm, time = %s, version = %s" % (
                positional_verification_result['result'],
                positional_verification_result['verification_millimeter'],
                positional_verification_result['time'],
                positional_verification_result['algorithm_version']), file=outfile)
            
            print("Positional verification: calibration_pars = %r" % 
                  positional_verification_result['calibration_pars'], file=outfile)
            
            print("Positional verification: analysis_results = %r" % 
                  positional_verification_result['analysis_results'], file=outfile)
            
            print("Positional verification: gearbox_correction = %r" % 
                  positional_verification_result['gearbox_correction'], file=outfile)
            
            print("Positional verification: posver_errors = %r" % 
                  positional_verification_result['posver_errors'], file=outfile)
        else:
            print("Positional verification: message = %s, time = %s, version = %s" % (err_msg,
                positional_verification_result['time'],
                positional_verification_result['algorithm_version']), file=outfile)

    if pupil_alignment_result is None:
        print("pupil_alignment test: n/a", file=outfile)
    else:
        err_msg = pupil_alignment_result['error_message']
        if len(err_msg) == 0:
            print("pupil alignment: passed = %s, measures= %r, time = %s" % (
                pupil_alignment_result['result'],
                pupil_alignment_result['measures'],
                pupil_alignment_result['time']), file=outfile)
            print("pupil alignment: coords = %r" %
                   pupil_alignment_result['coords'], file=outfile)
            print("pupil alignment: calibration_pars = %r" %
                   pupil_alignment_result['calibration_pars'], file=outfile)
        else:
            print("pupil alignment: message = %s, time = %s" %
                  (err_msg,
                   pupil_alignment_result['time']), file=outfile)
    
def report(env, vfdb, gd, grid_state, opts, eval_fpuset, fpu_config):

    for count, fpu_id in enumerate(eval_fpuset):
        ddict = get_data(env, vfdb, gd, grid_state, opts, fpu_id, fpu_config)

        if count > 0:
            print("\n", file=opts.output_file)

        if opts.report_format == 'terse':
            print_report_terse(**ddict)
        elif opts.report_format == 'long':
            print_report_long(**ddict)
        else:
            raise ValueError("option not implemented")


        
def dump_data(env, vfdb, gd, grid_state, opts, eval_fpuset, fpu_config):

    print("{", file=opts.output_file)
    for count, fpu_id in enumerate(eval_fpuset):
        ddict = get_data(env, vfdb, gd, grid_state, opts, fpu_id, fpu_config)
        if count > 0:
            print("\n\n", file=opts.output_file)
        print("%r : %r," % (fpu_id, ddict), file=opts.output_file)
        


    print("}", file=opts.output_file)
