from __future__ import print_function, division

from numpy import zeros

from FpuGridDriver import (CAN_PROTOCOL_VERSION, SEARCH_CLOCKWISE, SEARCH_ANTI_CLOCKWISE,
                           DEFAULT_WAVEFORM_RULSET_VERSION, DATUM_TIMEOUT_DISABLE,
                           DASEL_BOTH, DASEL_ALPHA, DASEL_BETA,
                           # see documentation reference for Exception hierarchy
                           # (for CAN protocol 1, this is section 12.6.1)
                           EtherCANException, MovementError, CollisionError, LimitBreachError, FirmwareTimeoutError,
                           AbortMotionError, StepTimingError, InvalidStateException, SystemFailure,
                           InvalidParameterError, SetupError, InvalidWaveformException, ConnectionFailure,
                           SocketFailure, CommandTimeout, ProtectionError, HardwareProtectionError)

from fpu_commands import *
from fpu_constants import *

from vfr.tests_common import flush, timestamp

def dirac(n, L):
    """return vector of length L with all zeros except a one at position n.
    """
    v = zeros(L, dtype=float)
    v[n] = 1.0
    return v

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
            fsuccess = (((dasel == DASEL_ALPHA) and a_ok)
                        or ((dasel == DASEL_BETA) and b_ok)
                        or ((dasel == DASEL_BOTH) and a_ok and b_ok)) 

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

def goto_position(gd, abs_alpha, abs_beta, fpuset, grid_state, allow_uninitialized=False, soft_protection=True):
        current_angles = gd.trackedAngles(grid_state, retrieve=True)
        current_alpha = array([x.as_scalar() for x, y in current_angles ])
        current_beta = array([y.as_scalar() for x, y in current_angles ])
        gd.pingFPUs(grid_state)
        print("current positions:\nalpha=%r,\nbeta=%r" % (current_alpha, current_beta))
              
        print("moving to (%6.2f,%6.2f)" % (abs_alpha, abs_beta))
        
        wf = gen_wf(- current_alpha + abs_alpha, - current_beta + abs_beta)
        wf = { k : v for k, v in wf.items() if k in fpuset }
        gd.configMotion(wf, grid_state, allow_uninitialized=allow_uninitialized,
                        soft_protection=soft_protection, warn_unsafe=soft_protection)
        
        gd.executeMotion(grid_state, fpuset=fpuset)

        if CAN_PROTOCOL_VERSION == 1:
            gd.pingFPUs(grid_state)

            
def test_datum(env, vfdb, gd, grid_state, args, fpuset, fpu_config, dasel=DASEL_BOTH):
    
    gd.pingFPUs(grid_state, fpuset=fpuset)

    # depending on options, we reset & rewind the FPUs
    if args.alwaysResetFPUs:
        print("resetting FPUs.... ", end='')
        flush()
        gd.resetFPUs(grid_state, fpuset=fpuset)
        print("OK")

    abs_alpha = -180.0 + 1.5
    abs_beta = 1.5
    if args.rewind_fpus:
        goto_position(gd, abs_alpha, abs_beta, fpuset, grid_state,
                      allow_uninitialized=True)
    
    
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
    except (FirmwareTimeoutError, CollisionError, MovementError) as e:
        success = False
        valid = True
        rigstate = str(e)
    except (InvalidStateException, ConnectionFailure) as e:
        success = False
        valid = False
        rigstate = str(e)
    print("findDatum finished, success=%s, rigstate=%s" % (success, rigstate))

    if valid:
        save_datum_result(env, vfdb, args, fpu_config, fpuset, dasel,
                          grid_state, rigstate)
                      
    
def test_limit(env, fpudb, vfdb, gd, grid_state, args, fpuset, fpu_config, which_limit):
    abs_alpha_def = -180.0
    abs_beta_def = 0.0
    goto_position(gd, abs_alpha_def, abs_beta_def, fpuset, grid_state)

    if which_limit == "alpha_max":
        abs_alpha, abs_beta = 180.0, 0.0
        dw = -30
        idx = 0
    elif which_limit == "alpha_min":
        abs_alpha, abs_beta = -190.0, 0.0
        dw = 30
        idx = 0
    elif which_limit == "beta_max":
        abs_alpha, abs_beta = 0.0, 180.0
        idx = 1
    elif which_limit == "beta_min":
        abs_alpha, abs_beta = 0.0, -180.0
        idx = 1

    for fpu_id in fpuset:
        try:
            print("limit test %s: moving fpu %i to position (%6.2f, %6.2f)" % (
                which_limit, fpu_id, abs_alpha, abs_beta))
            
            goto_position(gd, abs_alpha, abs_beta, [fpu_id], grid_state, soft_protection=False)
            test_succeeded = False
            test_valid = True
            diagnostic = "detection failed"
            
        except (LimitBreachError, CollisionError) as e:
            test_succeeded = True
            test_valid = True
            diagnostic = "correctly detected"
            print("detected : ", str(e))
            
        except MovementError as e:
            test_succeeded = None
            test_valid = False
            diagnostic = str(e)
    
        print("FPU %i test result: valid=%s, succeeded=%r, diagnostic=%s" % (
            fpu_id, test_valid, test_succeeded, diagnostic))
        
        if test_succeeded:
            gd.pingFPUs(grid_state, fpuset=[fpu_id])
            limit_val = (gd.trackedAngles(grid_state, retrieve=True)[fpu_id][idx]).as_scalar()
            print("%s limit hit at position %f" % (which_limit, limit_val))
        

        N = args.N
        if which_limit in ["alpha_max", "alpha_min"]:
            print("moving fpu %i back by %i" % (fpu_id, dw))
            gd.resetFPUs(grid_state, [fpu_id])
            wf = gen_wf(dw * dirac(fpu_id,N) , 0)
            gd.configMotion(wf, grid_state, soft_protection=False, warn_unsafe=False, allow_uninitialized=True)
            gd.executeMotion(grid_state, fpuset=[fpu_id])
            

        # bring fpu back to default position
        goto_position(gd, abs_alpha_def, abs_beta_def, [fpu_id], grid_state, allow_uninitialized=True)
        print("searching datum for FPU %i, to resolve collision" % fpu_id)
        gd.findDatum(grid_state, fpuset=[fpu_id])
        
        
            
