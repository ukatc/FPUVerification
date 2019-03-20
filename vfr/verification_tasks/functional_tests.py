from __future__ import print_function, division

from numpy import NaN

from FpuGridDriver import (
    CAN_PROTOCOL_VERSION,
    SEARCH_CLOCKWISE,
    SEARCH_ANTI_CLOCKWISE,
    DEFAULT_WAVEFORM_RULSET_VERSION,
    DATUM_TIMEOUT_DISABLE,
    DASEL_BOTH,
    DASEL_ALPHA,
    DASEL_BETA,
    REQD_ANTI_CLOCKWISE,
    REQD_CLOCKWISE,
    # see documentation reference for Exception hierarchy
    # (for CAN protocol 1, this is section 12.6.1)
    EtherCANException,
    MovementError,
    CollisionError,
    LimitBreachError,
    FirmwareTimeoutError,
    AbortMotionError,
    StepTimingError,
    InvalidStateException,
    SystemFailure,
    InvalidParameterError,
    SetupError,
    InvalidWaveformException,
    ConnectionFailure,
    SocketFailure,
    CommandTimeout,
    ProtectionError,
    HardwareProtectionError,
)

from fpu_commands import gen_wf


from vfr.db.datum import TestResult, save_datum_result
from vfr.db.colldect_limits import (
    save_angular_limit,
    set_protection_limit,
    get_anglimit_passed_p,
)



from vfr.tests_common import flush, timestamp, dirac, goto_position, get_sorted_positions

from vfr import hw
from vfr import hwsimulation as hws

from vfr.turntable import go_collision_test_pos


def test_datum(ctx, dasel=DASEL_BOTH):

    ctx.gd.pingFPUs(ctx.grid_state, fpuset=ctx.measure_fpuset)

    # depending on options, we reset & rewind the FPUs
    if ctx.opts.alwaysResetFPUs:
        print ("resetting FPUs.... ", "end=' '")
        flush()
        ctx.gd.resetFPUs(ctx.grid_state, fpuset=ctx.measure_fpuset)
        print ("OK")

    abs_alpha = -180.0 + 1.5
    abs_beta = 1.5
    if ctx.opts.rewind_fpus:
        goto_position(
            ctx.gd,
            abs_alpha,
            abs_beta,
            ctx.grid_state,
            fpuset=ctx.measure_fpuset,
            allow_uninitialized=True,
        )

    # Now, we issue a findDatum method. In order to know when and how
    # this command finished, we pass the ctx.grid_state variable.

    modes = {fpu_id: SEARCH_CLOCKWISE for fpu_id in ctx.measure_fpuset}
    print ("issuing findDatum (%s):" % dasel)
    try:
        ctx.gd.findDatum(
            ctx.grid_state,
            timeout=DATUM_TIMEOUT_DISABLE,
            search_modes=modes,
            selected_arm=dasel,
            fpuset=ctx.measure_fpuset,
        )
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
    print ("findDatum finished, success=%s, rigstate=%s" % (success, rigstate))

    if valid:
        save_datum_result(ctx, dasel, rigstate)


def test_limit(ctx, which_limit, pars=None):

    tstamp = timestamp()
    if ctx.opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hws

    abs_alpha_def = -180.0
    abs_beta_def = 0.0
    goto_position(
        ctx.gd, abs_alpha_def, abs_beta_def, ctx.grid_state, fpuset=ctx.measure_fpuset
    )

    if which_limit == "alpha_min":
        abs_alpha, abs_beta = pars.LIMIT_ALPHA_NEG_EXPECT, 0.0
        dw = 30
        idx = 0
    elif which_limit == "alpha_max":
        abs_alpha, abs_beta = pars.LIMIT_ALPHA_POS_EXPECT, 0.0
        dw = -30
        idx = 0
    elif which_limit == "beta_min":
        abs_alpha, abs_beta = pars.LIMIT_BETA_NEG_EXPECT, -180.0
        free_dir = REQD_ANTI_CLOCKWISE
        dw = 30
        idx = 1
    elif which_limit == "beta_max":
        abs_alpha, abs_beta = pars.LIMIT_BETA_POS_EXPECT, 180.0
        free_dir = REQD_CLOCKWISE
        dw = -30
        idx = 1
    elif which_limit == "beta_collision":
        abs_alpha, abs_beta = pars.COLDECT_ALPHA, (pars.COLDECT_BETA + 5.0)
        free_dir = REQD_CLOCKWISE
        dw = 30
        idx = 1

    if which_limit != "beta_collision":
        # home turntable
        hw.safe_home_turntable(ctx.gd, ctx.grid_state)


    for fpu_id, stage_position in get_sorted_positions(
        ctx.measure_fpuset, pars.COLDECT_POSITIONS
    ):
        sn = ctx.fpu_config[fpu_id]["serialnumber"]

        if get_anglimit_passed_p(
            ctx, fpu_id, sn, which_limit,
        ) and (not ctx.opts.repeat_passed_tests):

            print (
                "FPU %s : limit test %r already passed, skipping test"
                % (sn, which_limit)
            )
            continue

        try:
            if which_limit == "beta_collision":
                # home turntable
                hw.safe_home_turntable(ctx.gd, ctx.grid_state)
                go_collision_test_pos(fpu_id, ctx.opts)

            print (
                "limit test %s: moving fpu %i to position (%6.2f, %6.2f)"
                % (which_limit, fpu_id, abs_alpha, abs_beta)
            )

            if which_limit == "beta_collision":
                # move rotary stage to POS_REP_POSN_N
                hw.turntable_safe_goto(ctx.gd, ctx.grid_state, stage_position)

            if which_limit == "beta_collision":
                goto_position(
                    ctx.gd,
                    abs_alpha,
                    abs_beta - 5.0,
                    ctx.grid_state,
                    fpuset=[fpu_id],
                    soft_protection=False,
                )
                goto_position(
                    ctx.gd,
                    abs_alpha,
                    abs_beta + 5.0,
                    ctx.grid_state,
                    fpuset=[fpu_id],
                    soft_protection=False,
                )

            else:
                goto_position(
                    ctx.gd,
                    abs_alpha,
                    abs_beta,
                    ctx.grid_state,
                    fpuset=[fpu_id],
                    soft_protection=False,
                )

            test_succeeded = False
            test_valid = True
            diagnostic = "detection failed"

        except (LimitBreachError, CollisionError) as e:
            test_succeeded = True
            test_valid = True
            diagnostic = "correctly detected"
            print ("detected : ", str(e))

        except MovementError as e:
            test_succeeded = False
            test_valid = False
            diagnostic = str(e)

        print (
            "FPU %i test result: valid=%s, succeeded=%r, diagnostic=%s"
            % (fpu_id, test_valid, test_succeeded, diagnostic)
        )

        if test_succeeded:
            ctx.gd.pingFPUs(ctx.grid_state, fpuset=[fpu_id])
            limit_val = (
                ctx.gd.trackedAngles(ctx.grid_state, retrieve=True)[fpu_id][idx]
            ).as_scalar()
            print ("%s limit hit at position %f" % (which_limit, limit_val))
        else:
            limit_val = NaN

        if test_valid:
            save_angular_limit(
                ctx,
                fpu_id,
                sn,
                which_limit,
                test_succeeded,
                limit_val,
                diagnostic,
            )

        if test_valid and test_succeeded and (which_limit != "beta_collision"):
            set_protection_limit(ctx, fpu_id, which_limit, limit_val)

        if test_succeeded:
            # bring FPU back into valid range and protected state
            N = ctx.opts.N
            if which_limit in ["alpha_max", "alpha_min"]:
                print ("moving fpu %i back by %i degree" % (fpu_id, dw))
                ctx.gd.resetFPUs(ctx.grid_state, [fpu_id])
                wf = gen_wf(dw * dirac(fpu_id, N), 0)
                ctx.gd.configMotion(
                    wf,
                    ctx.grid_state,
                    soft_protection=False,
                    warn_unsafe=False,
                    allow_uninitialized=True,
                )
                ctx.gd.executeMotion(ctx.grid_state, fpuset=[fpu_id])
            else:
                print ("moving fpu %i back by %i steps" % (fpu_id, 10))
                for k in range(3):
                    ctx.gd.freeBetaCollision(
                        fpu_id, free_dir, ctx.grid_state, soft_protection=False
                    )
                    ctx.gd.pingFPUs(ctx.grid_state, [fpu_id])
                ctx.gd.enableBetaCollisionProtection(ctx.grid_state)
                wf = gen_wf(0, dw * dirac(fpu_id, N))
                ctx.gd.configMotion(
                    wf,
                    ctx.grid_state,
                    soft_protection=False,
                    warn_unsafe=False,
                    allow_uninitialized=True,
                )
                ctx.gd.executeMotion(ctx.grid_state, fpuset=[fpu_id])

        # bring fpu back to default position
        goto_position(
            ctx.gd,
            abs_alpha_def,
            abs_beta_def,
            ctx.grid_state,
            fpuset=[fpu_id],
            allow_uninitialized=True,
        )
        print ("searching datum for FPU %i, to resolve collision" % fpu_id)
        ctx.gd.findDatum(ctx.grid_state, fpuset=[fpu_id])

    if which_limit == "beta_collision":
        # home turntable
        hw.safe_home_turntable(ctx.gd, ctx.grid_state)
