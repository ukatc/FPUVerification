from __future__ import print_function, division

from numpy import zeros, nan
from protectiondb import ProtectionDB as pdb
from vfr.db import save_test_result, TestResult
from vfr import turntable

from interval import Interval


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

from vfr.tests_common import flush, timestamp, dirac, goto_position



    

def  save_datum_result(env, vfdb, args, fpu_config, fpuset, dasel, grid_state, rigstate):

    # define two closures - one for the unique key, another for the stored value 
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]['serialnumber']
        keybase = (serialnumber, 'findDatum', str(dasel))
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
        goto_position(gd, abs_alpha, abs_beta, grid_state, fpuset=fpuset,
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
                      

def save_angular_range(env, vfdb, fpu_id, serialnumber, which_limit,
                       test_succeeded, limit_val, verbosity=2):
    
    print("saving limit value")


    def keyfunc(fpu_id):
        if which_limit == "beta_collision":
            keybase = (serialnumber, which_limit)
        else:
            keybase = (serialnumber, 'limit', which_limit)
        return keybase

    def valfunc(fpu_id):

        if test_succeeded:
            fsuccess = TestResult.OK
        else:
            fsuccess = TestResult.FAILED
            
        val = repr({'result' : fsuccess,                    
                    'val' : limit_val,                    
                    'time' : timestamp()})
        return val

    
    save_test_result(env, vfdb, [fpu_id], keyfunc, valfunc, verbosity=verbosity)
    
    

def set_protection_limit(env, fpudb, fpu, serialnumber, which_limit, measured_val,
                         protection_tolerance, update):

    """This replaces the corresponding entry in the protection database if
    either the update flag is True, or the current entry is the default value.
    """
    if which_limit in [ "alpha_max", "alpha_min"]:
        subkey = pdb.alpha_limits
        offset = ALPHA_DATUM_OFFSET        
        default_min, default_max = ALPHA_MIN_DEGREE, ALPHA_MAX_DEGREE
    else:
        subkey = pdb.beta_limits
        offset = 0.0
        default_min, default_max = BETA_MIN_DEGREE, BETA_MAX_DEGREE

    is_min = which_limit in [ "beta_min", "alpha_min"]

    if is_min:
        default_val = default_min
    else:
        default_val = default_max
        

    with env.begin(write=True,db=fpudb) as txn:
        val = pdb.getField(txn, fpu, subkey) + offset

        val_min = val.min()
        val_max = val.max()
        if is_min:
            if (val_min == default_val) or update:
                val_min = measured_val + protection_tolerance
        else:
            if (val_max == default_val) or update:
                val_max = measured_val - protection_tolerance
    
        
        new_val = Interval(val_min, val_max)
        print("limit %s: replacing %r by %r" % (which_limit, val, new_val))
        pdb.putInterval(txn, serialnumber, subkey, new_val, offset)


    
def test_limit(env, fpudb, vfdb, gd, grid_state, args, fpuset, fpu_config, which_limit):
    abs_alpha_def = -180.0
    abs_beta_def = 0.0
    goto_position(gd, abs_alpha_def, abs_beta_def, grid_state, fpuset=fpuset)

    if which_limit == "alpha_max":
        abs_alpha, abs_beta = 180.0, 0.0
        dw = -30
        idx = 0
    elif which_limit == "alpha_min":
        abs_alpha, abs_beta = -190.0, 0.0
        dw = 30
        idx = 0
    elif which_limit == "beta_max":
        abs_alpha, abs_beta = -180.0, 180.0
        free_dir = REQD_CLOCKWISE
        dw = -30
        idx = 1
    elif which_limit == "beta_min":
        abs_alpha, abs_beta = -180.0, -180.0
        free_dir = REQD_ANTI_CLOCKWISE
        dw = 30
        idx = 1
    elif which_limit == "beta_collision":
        abs_alpha, abs_beta = -180.0, 90.0
        free_dir = REQD_CLOCKWISE
        dw = 30
        idx = 1

    for fpu_id in fpuset:
        try:
            print("limit test %s: moving fpu %i to position (%6.2f, %6.2f)" % (
                which_limit, fpu_id, abs_alpha, abs_beta))

            if which_limit == "beta_collision":
                turntable.go_collision_test_pos(fpu_id, args)
            
            goto_position(gd, abs_alpha, abs_beta, grid_state, fpuset=[fpu_id], soft_protection=False)
            test_succeeded = False
            test_valid = True
            diagnostic = "detection failed"
            
        except (LimitBreachError, CollisionError) as e:
            test_succeeded = True
            test_valid = True
            diagnostic = "correctly detected"
            print("detected : ", str(e))
            
        except MovementError as e:
            test_succeeded = False
            test_valid = False
            diagnostic = str(e)
    
        print("FPU %i test result: valid=%s, succeeded=%r, diagnostic=%s" % (
            fpu_id, test_valid, test_succeeded, diagnostic))
        
        if test_succeeded:
            gd.pingFPUs(grid_state, fpuset=[fpu_id])
            limit_val = (gd.trackedAngles(grid_state, retrieve=True)[fpu_id][idx]).as_scalar()
            print("%s limit hit at position %f" % (which_limit, limit_val))
        else:
            limit_val = nan

        sn = fpu_config[fpu_id]['serialnumber']
        
        if test_valid:
            save_angular_range(env, vfdb, fpu_id, sn, which_limit, test_succeeded, limit_val, verbosity=3)

        if test_valid and test_succeeded and (which_limit != "beta_collision"):
            set_protection_limit(env, fpudb, grid_state.FPU[fpu_id],
                                 sn, which_limit, limit_val,
                                 args.protection_tolerance, args.update_protection_limits)
            
        
        if test_succeeded:
            # bring FPU back into valid range and protected state
            N = args.N
            if which_limit in ["alpha_max", "alpha_min"]:
                print("moving fpu %i back by %i degree" % (fpu_id, dw))
                gd.resetFPUs(grid_state, [fpu_id])
                wf = gen_wf(dw * dirac(fpu_id,N) , 0)
                gd.configMotion(wf, grid_state, soft_protection=False, warn_unsafe=False, allow_uninitialized=True)
                gd.executeMotion(grid_state, fpuset=[fpu_id])
            else:
                print("moving fpu %i back by %i steps" % (fpu_id, 10))
                for k in range(3):
                    gd.freeBetaCollision(fpu_id, free_dir, grid_state, soft_protection=False)
                    gd.pingFPUs(grid_state, [fpu_id])
                gd.enableBetaCollisionProtection(grid_state)
                wf = gen_wf(0, dw * dirac(fpu_id,N))
                gd.configMotion(wf, grid_state, soft_protection=False, warn_unsafe=False, allow_uninitialized=True)
                gd.executeMotion(grid_state, fpuset=[fpu_id])
            
            

        # bring fpu back to default position
        goto_position(gd, abs_alpha_def, abs_beta_def, grid_state,
                      fpuset=[fpu_id], allow_uninitialized=True)
        print("searching datum for FPU %i, to resolve collision" % fpu_id)
        gd.findDatum(grid_state, fpuset=[fpu_id])
        
        
            
