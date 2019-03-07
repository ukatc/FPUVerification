from __future__ import print_function, division

from numpy import zeros, nan
from protectiondb import ProtectionDB as pdb
from vfr.db.datum import env, TestResult, save_datum_result
from vfr.db.colldect_limits import save_angular_limit, set_protection_limit, get_anglimit_passed_p
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



    

    


            
def test_datum(env, vfdb, gd, grid_state, opts, fpuset, fpu_config, dasel=DASEL_BOTH):
    
    gd.pingFPUs(grid_state, fpuset=fpuset)

    # depending on options, we reset & rewind the FPUs
    if opts.alwaysResetFPUs:
        print("resetting FPUs.... ", end='')
        flush()
        gd.resetFPUs(grid_state, fpuset=fpuset)
        print("OK")

    abs_alpha = -180.0 + 1.5
    abs_beta = 1.5
    if opts.rewind_fpus:
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
        save_datum_result(env, vfdb, opts, fpu_config, fpuset, dasel,
                          grid_state, rigstate)
                      



    
def test_limit(env, fpudb, vfdb, gd, grid_state, opts, fpuset, fpu_config, which_limit):
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
        sn = fpu_config[fpu_id]['serialnumber']
        
        if (get_anglimit_passed_p(env, vfdb, fpu_id, sn, which_limit,
                                  verbosity=opts.verbosity) and (
                                      not opts.repeat_passed_tests)):
            
            print("FPU %s : limit test %r already passed, skipping test" % (sn, which_limit))
            continue
            

        try:
            print("limit test %s: moving fpu %i to position (%6.2f, %6.2f)" % (
                which_limit, fpu_id, abs_alpha, abs_beta))

            if which_limit == "beta_collision":
                turntable.go_collision_test_pos(fpu_id, opts)
            
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

        
        if test_valid:
            save_angular_limit(env, vfdb, fpu_id, sn, which_limit, test_succeeded, limit_val, verbosity=3)

        if test_valid and test_succeeded and (which_limit != "beta_collision"):
            set_protection_limit(env, fpudb, grid_state.FPU[fpu_id],
                                 sn, which_limit, limit_val,
                                 opts.protection_tolerance, opts.update_protection_limits)
            
        
        if test_succeeded:
            # bring FPU back into valid range and protected state
            N = opts.N
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
        
        
            
