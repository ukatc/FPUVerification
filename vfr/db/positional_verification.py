from __future__ import print_function, division,  absolute_import

from db.base import env, GIT_VERSION, TestResult, get_test_result 

def  save_positional_verification_images(env, vfdb, args, fpu_config, fpu_id, images_dict):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, 'positional-verification', 'images')
        return keybase

    def valfunc(fpu_id):
        
                        
        val = repr({'fpuid' : fpu_id,
                    'images' : image_dict),
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=args.verbosity)


def  get_positional_verification_images(env, vfdb, args, fpu_config, fpu_id):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, 'positional-verification', 'images')
        return keybase

    return get_test_result(env, vfdb, fpuset, keyfunc, verbosity=args.verbosity)
    
    
def  save_positional_verification_result(env, vfdb, args, fpu_config, fpu_id,
                                         pos_rep_calibration_pars=None,
                                         analysis_results=None,
                                         posver_errors=None,
                                         positional_verification_mm=None,
                                         errmsg="",
                                         positional_verification_has_passed=None):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, 'positional-verification', 'result')
        return keybase

    def valfunc(fpu_id):
        
                        
        val = repr({'calibration_pars' : pos_rep_calibration_pars,
                    'analysis_results' : analysis_results,
                    'verification_millimeter' : positional_verification_mm,
                    'result' : positional_verification_has_passed,
                    'posver_errors' : posver_errors,
                    'error_message' : errmsg,
                    'git-version' : GIT_VERSION,
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=args.verbosity)
