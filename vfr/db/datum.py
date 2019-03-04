from __future__ import print_function, division,  absolute_import

from db.base import env, GIT_VERSION, TestResult, get_test_result 

RECORD_TYPE = 'findDatum'

def  save_datum_result(env, vfdb, args, fpu_config, fpuset, dasel, grid_state, rigstate):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, RECORD_TYPE, str(dasel))
        return keybase

    def valfunc(fpu_id):
        
        if CAN_PROTOCOL_VERSION == 1:
            a_ok = grid_state.FPU[fpu_id].alpha_was_zeroed
            b_ok = grid_state.FPU[fpu_id].beta_was_zeroed
        else:
            a_ok = grid_state.FPU[fpu_id].alpha_was_calibrated
            b_ok = grid_state.FPU[fpu_id].beta_was_calibrated
        
        print("%i : (alpha datumed=%s, beta datumed = %s)" % (fpu_id, a_ok, b_ok))
        
        if (((dasel == DASEL_ALPHA) and a_ok)
            or ((dasel == DASEL_BETA) and b_ok)
            or ((dasel == DASEL_BOTH) and a_ok and b_ok)):
            
            fsuccess = TestResult.OK
        else:
            fsuccess = TestResult.FAILED
                        
        val = repr({'result' : fsuccess,
                    'datumed' : (a_ok, b_ok),
                    'fpuid' : fpu_id,
                    'result_state' : str(grid_state.FPU[fpu_id].state),
                    'diagnostic' : "OK" if fsuccess else rigstate,
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=args.verbosity)


def  get_datum_result(env, vfdb, args, fpu_config, fpu_id):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, RECORD_TYPE, 'result')
        return keybase
    
    return get_test_result(env, vfdb, fpuset, keyfunc, verbosity=args.verbosity)

def  get_datum_passed_p(env, vfdb, args, fpu_config, fpu_id):
    """returns True if the latest datum repetability test for this FPU
    was passed successfully."""
    
    val = get_datum_result(env, vfdb, args, fpu_config, fpu_id)

    if val is None:
        return False
    
    return (val['result'] == TestResult.OK)
    
