from __future__ import print_function, division,  absolute_import

from db.base import env, GIT_VERSION, TestResult, get_test_result 

RECORD_TYPE='positional-repeatability'

def  save_positional_repeatability_images(env, vfdb, args, fpu_config, fpu_id, images_dict):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, RECORD_TYPE, 'images')
        return keybase

    def valfunc(fpu_id):
        
                        
        val = repr({'fpuid' : fpu_id,
                    'images' : image_dict),
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=args.verbosity)


def  get_positional_repeatability_images(env, vfdb, args, fpu_config, fpu_id):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, RECORD_TYPE, 'images')
        return keybase

    return get_test_result(env, vfdb, fpuset, keyfunc, verbosity=args.verbosity)
    
    
def  save_positional_repeatability_result(env, vfdb, args, fpu_config, fpu_id,
                                          pos_rep_calibration_pars=None,
                                          analysis_results=None,
                                          positional_repeatability_mm=None,
                                          gearbox_correction={},
                                          errmsg="",
                                          positional_repeatability_has_passed=None):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, RECORD_TYPE, 'result')
        return keybase

    def valfunc(fpu_id):
        
                        
        val = repr({'calibration_pars' : pos_rep_calibration_pars,
                    'analysis_results' : analysis_results,
                    'repeatability_millimeter' : positional_repeatability_mm,
                    'result' : positional_repeatability_has_passed,
                    'gearbox_correction' : gearbox_correction,
                    'error_message' : errmsg,
                    'git-version' : GIT_VERSION,
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=args.verbosity)
    


def  get_positional_repeatability_result(env, vfdb, args, fpu_config, fpu_id):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, RECORD_TYPE, 'result')
        return keybase

    
    return get_test_result(env, vfdb, fpuset, keyfunc, verbosity=args.verbosity)

    
def  get_positional_repeatability_passed_p(env, vfdb, args, fpu_config, fpu_id):
    """returns True if the latest positional repetability test for this FPU
    was passed successfully."""
    
    val = get_positional_repeatability_result(env, vfdb, args, fpu_config, fpu_id)

    if val is None:
        return False
    
    return (val['result'] == TestResult.OK)
