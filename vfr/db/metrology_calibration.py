from __future__ import print_function, division,  absolute_import

from numpy import NaN

from vfr.db.base import GIT_VERSION, TestResult, get_test_result, timestamp  

RECORD_TYPE = 'metrology-calibration'

def  save_metrology_calibration_images(env, vfdb, opts, fpu_config, fpu_id, images):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, RECORD_TYPE, 'images')
        return keybase

    def valfunc(fpu_id):
        
                        
        val = repr({'fpuid' : fpu_id,
                    'images' : images,
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=opts.verbosity)


def  get_metrology_calibration_images(env, vfdb, opts, fpu_config, fpu_id):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, RECORD_TYPE, 'images')
        return keybase

    return get_test_result(env, vfdb, fpuset, keyfunc, verbosity=opts.verbosity)
    
    
def  save_metrology_calibration_result(env, vfdb, opts, fpu_config, fpu_id,
                                       coords=None, 
                                       metcal_fibre_large_target_distance=NaN,
                                       metcal_fibre_small_target_distance=NaN,
                                       metcal_target_vector_angle=NaN,
                                       errmsg="",
                                       analysis_version=None):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, RECORD_TYPE, 'result')
        return keybase

    def valfunc(fpu_id):
        
                        
        val = repr({'coords' : coords,
                    'fibre_distance' : fibre_distance,
                    'metcal_fibre_large_target_distance' : metcal_fibre_large_target_distance, 
                    'metcal_fibre_small_target_distance' : metcal_fibre_small_target_distance,
                    'metcal_target_vector_angle' : metcal_target_vector_angle,
                    'error_message' : errmsg,
                    'algorithm_version' : analysis_version,
                    'git_version' : GIT_VERSION,
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=opts.verbosity)

def  get_metrology_calibration_result(env, vfdb, opts, fpu_config, fpu_id):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, RECORD_TYPE, 'result')
        return keybase
    
    return get_test_result(env, vfdb, fpuset, keyfunc, verbosity=opts.verbosity)

    
