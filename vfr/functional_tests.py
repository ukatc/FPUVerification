from __future__ import print_function, division


from FpuGridDriver import (CAN_PROTOCOL_VERSION, SEARCH_CLOCKWISE, SEARCH_ANTI_CLOCKWISE,
                           DEFAULT_WAVEFORM_RULSET_VERSION, DATUM_TIMEOUT_DISABLE,
                           DASEL_BOTH, DASEL_ALPHA, DASEL_BETA,
                           FirmwareTimeoutError, CollisionError, InvalidStateException)

from fpu_commands import *
from fpu_constants import *

from vfr.tests_common import flush, timestamp


def rewind_fpus(gd, grid_state, args):

    # Now, we issue a findDatum method. In order to know when and how
    # this command finished, we pass the grid_state variable.

    if args.rewind_fpus:
        current_angles = gd.trackedAngles(grid_state, retrieve=True)
        current_alpha = array([x.as_scalar() for x, y in current_angles ])
        current_beta = array([y.as_scalar() for x, y in current_angles ])
        print("current positions:\nalpha=%r,\nbeta=%r" % (current_alpha, current_beta))
              
        if False :
              
            print("moving close to datum switch")
            wf = gen_wf(- current_alpha + 0.5, - current_beta + 0.5)
            gd.configMotion(wf, grid_state, allow_uninitialized=True)
            gd.executeMotion(grid_state)
            
    return grid_state


def find_datum(gd, grid_state, args):
    
    print("issuing findDatum:")
    gd.findDatum(grid_state, timeout=DATUM_TIMEOUT_DISABLE)
    print("findDatum finished")

    # We can use grid_state to display the starting position
    print("the starting position (in degrees) is:", gd.trackedAngles(grid_state, retrieve=True))

    return gd, grid_state


def  save_datum_result(env, vfdb, args, fpu_config, fpuset, dasel, grid_state, rigstate):
    
    with env.begin(write=True,db=vfdb) as txn:
            
        for fpu_id in fpuset:
            if CAN_PROTOCOL_VERSION == 1:
                a_ok = grid_state.FPU[fpu_id].alpha_was_zeroed
                b_ok = grid_state.FPU[fpu_id].beta_was_zeroed
            else:
                a_ok = grid_state.FPU[fpu_id].alpha_was_calibrated
                b_ok = grid_state.FPU[fpu_id].beta_was_calibrated
            
            print("%i : (alpha datumed=%s, beta datumed = %s)" % (fpu_id, a_ok, b_ok))
        
            serialnumber = fpu_config[fpu_id]['serialnumber']
            key1 = repr( (serialnumber, 'findDatum', str(dasel), 'ntests') )
            last_cnt = txn.get(key1)
            if last_cnt is None:
                count = 0
            else:
                count = int(last_cnt) + 1
                
            key2 = repr( (serialnumber, 'findDatum', str(dasel), 'result', count) )
            fsuccess = ((DASEL_ALPHA and a_ok)
                        or (DASEL_BETA and b_ok)
                        or (DASEL_BOTH and a_ok and b_ok)) 

            if fsuccess:
                diagnostic = "OK"
            else:
                diagnostic = rigstate
                
            val = repr({'success' : fsuccess,
                        'dasel' : str(dasel),
                        'result' : (a_ok, b_ok),
                        'fpuid' : fpu_id,
                        'result_state' : str(grid_state.FPU[fpu_id].state),
                        'diagnostic' : diagnostic,
                        'time' : timestamp()})

            if args.verbosity > 2:
                print("putting %r : %r" % (key2, val))
                print("putting %r : %r" % (key1, str(count)))
            
            txn.put(key2, val)
            txn.put(key1, str(count))


def test_datum(env, vfdb, gd, grid_state, args, fpuset, fpu_config, dasel=DASEL_BOTH):
    
    gd.pingFPUs(grid_state, fpuset=fpuset)

    # depending on options, we reset & rewind the FPUs
    if args.alwaysResetFPUs:
        print("resetting FPUs.... ", end='')
        flush()
        gd.resetFPUs(grid_state, fpuset=fpuset)
        print("OK")
    
    if args.rewind_fpus:
        current_angles = gd.trackedAngles(grid_state, retrieve=True)
        current_alpha = array([x.as_scalar() for x, y in current_angles ])
        current_beta = array([y.as_scalar() for x, y in current_angles ])
        print("current positions:\nalpha=%r,\nbeta=%r" % (current_alpha, current_beta))
              
        print("moving close to datum switch")
        wf = gen_wf(- current_alpha + 1.5, - current_beta + 1.5)
        wf = { k : v for k, v in wf.items() if k in fpuset }
        gd.configMotion(wf, grid_state, allow_uninitialized=True)
        gd.executeMotion(grid_state, fpuset=fpuset)
    
    
    # Now, we issue a findDatum method. In order to know when and how
    # this command finished, we pass the grid_state variable.

    modes = { fpu_id : SEARCH_CLOCKWISE for fpu_id in fpuset }
    print("issuing findDatum (%s):" % dasel)
    try:
        gd.findDatum(grid_state, timeout=DATUM_TIMEOUT_DISABLE, search_modes=modes,
                     selected_arm=dasel, fpuset=fpuset)
        success = True
        valid = True
        rigstate = "OK"
    except (FirmwareTimeoutError, CollisionError) as e:
        success = False
        valid = True
        rigstate = str(e)
    except InvalidStateException as e:
        success = False
        valid = False
        rigstate = str(e)
    print("findDatum finished, success=%s, rigstate=%s" % (success, rigstate))

    if valid:
        save_datum_result(env, vfdb, args, fpu_config, fpuset, dasel,
                          grid_state, rigstate)
                      
    
