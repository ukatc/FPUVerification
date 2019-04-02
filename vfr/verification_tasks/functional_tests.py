from __future__ import absolute_import, division, print_function

from fpu_commands import gen_wf
from FpuGridDriver import (
    DASEL_ALPHA,
    DASEL_BETA,
    DASEL_BOTH,
    DATUM_TIMEOUT_DISABLE,
    REQD_ANTI_CLOCKWISE,
    REQD_CLOCKWISE,
    SEARCH_CLOCKWISE,
    CollisionError,
    ConnectionFailure,
    FirmwareTimeoutError,
    InvalidStateException,
    LimitBreachError,
    MovementError,
)
from numpy import NaN
from vfr.db.base import TestResult
from vfr.db.colldect_limits import (
    LimitTestResult,
    get_anglimit_passed_p,
    save_angular_limit,
    set_protection_limit,
)
from vfr.db.datum import save_datum_result
from vfr.tests_common import dirac, flush, get_sorted_positions, goto_position
from vfr.turntable import go_collision_test_pos

# calm down pyflakes static checker
assert DASEL_ALPHA or DASEL_BETA or True


class DatumFailure(Exception):
    pass


class CollisionDetectionFailure(Exception):
    pass


class LimitDetectionFailure(Exception):
    pass


def test_datum(rig, dbe, dasel=DASEL_BOTH):

    failed_fpus = []

    rig.gd.pingFPUs(rig.grid_state, fpuset=rig.measure_fpuset)

    # depending on options, we reset & rewind the FPUs
    if rig.opts.always_reset_fpus:
        print("resetting FPUs.... ", "end=' '")
        flush()
        rig.gd.resetFPUs(rig.grid_state, fpuset=rig.measure_fpuset)
        print("OK")

    abs_alpha = -180.0 + 1.5
    abs_beta = 1.5
    if rig.opts.rewind_fpus:
        goto_position(
            rig.gd,
            abs_alpha,
            abs_beta,
            rig.grid_state,
            fpuset=rig.measure_fpuset,
            allow_uninitialized=True,
        )

    # Now, we issue a findDatum method. In order to know when and how
    # this command finished, we pass the rig.grid_state variable.

    modes = {fpu_id: SEARCH_CLOCKWISE for fpu_id in rig.measure_fpuset}
    print("issuing findDatum (%s):" % dasel)
    try:
        rig.gd.findDatum(
            rig.grid_state,
            timeout=DATUM_TIMEOUT_DISABLE,
            search_modes=modes,
            selected_arm=dasel,
            fpuset=rig.measure_fpuset,
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

    print("findDatum finished, success=%s, rigstate=%s" % (success, rigstate))

    if valid:
        save_datum_result(rig, dbe, dasel, rigstate)

    for fpu_id, fpu in enumerate(rig.grid_state.FPU):
        if fpu_id not in rig.measure_fpuset:
            continue
        if not success:
            failed_fpus.append((fpu_id, rig.fpu_config[fpu_id]["serialnumber"]))

    if failed_fpus:
        raise DatumFailure("Datum test failed for FPUs %r" % failed_fpus)


def test_limit(rig, dbe, which_limit, pars=None):

    failed_fpus = []

    abs_alpha_def = -180.0
    abs_beta_def = 0.0
    goto_position(
        rig.gd,
        abs_alpha_def,
        abs_beta_def,
        rig.grid_state,
        fpuset=rig.measure_fpuset,
        verbosity=rig.opts.verbosity,
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
        abs_alpha, abs_beta = -180.0, pars.LIMIT_BETA_NEG_EXPECT
        free_dir = REQD_ANTI_CLOCKWISE
        dw = 30
        idx = 1
    elif which_limit == "beta_max":
        abs_alpha, abs_beta = -180.0, pars.LIMIT_BETA_POS_EXPECT
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
        rig.hw.safe_home_turntable(rig.gd, rig.grid_state)

    for fpu_id, stage_position in get_sorted_positions(
        rig.measure_fpuset, pars.COLDECT_POSITIONS
    ):
        sn = rig.fpu_config[fpu_id]["serialnumber"]

        if get_anglimit_passed_p(dbe, fpu_id, which_limit) and (
            not rig.opts.repeat_passed_tests
        ):

            print(
                "FPU %s : limit test %r already passed, skipping test"
                % (sn, which_limit)
            )
            continue

        try:
            if which_limit == "beta_collision":
                # home turntable
                print("pre-finding datum....")
                rig.gd.findDatum(rig.grid_state)
                print("OK")
                rig.hw.safe_home_turntable(rig.gd, rig.grid_state, opts=rig.opts)
                go_collision_test_pos(fpu_id, rig.opts)

            print(
                "limit test %s: moving fpu %i to position (%6.2f, %6.2f)"
                % (which_limit, fpu_id, abs_alpha, abs_beta)
            )

            if which_limit == "beta_collision":
                # move rotary stage to POS_REP_POSN_N
                rig.hw.turntable_safe_goto(rig.gd, rig.grid_state, stage_position)

            if which_limit == "beta_collision":
                goto_position(
                    rig.gd,
                    abs_alpha,
                    abs_beta - 5.0,
                    rig.grid_state,
                    fpuset=[fpu_id],
                    soft_protection=False,
                )
                goto_position(
                    rig.gd,
                    abs_alpha,
                    abs_beta + 5.0,
                    rig.grid_state,
                    fpuset=[fpu_id],
                    soft_protection=False,
                )

            else:
                goto_position(
                    rig.gd,
                    abs_alpha,
                    abs_beta,
                    rig.grid_state,
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
            print("detected : ", str(e))

        except MovementError as e:
            test_succeeded = False
            test_valid = False
            diagnostic = str(e)
            failed_fpus.append((fpu_id, rig.fpu_config[fpu_id]["serialnumber"]))

        print(
            "FPU %i test result: valid=%s, succeeded=%r, diagnostic=%s"
            % (fpu_id, test_valid, test_succeeded, diagnostic)
        )

        if test_succeeded:
            rig.gd.pingFPUs(rig.grid_state, fpuset=[fpu_id])
            limit_val = (
                rig.gd.trackedAngles(rig.grid_state, retrieve=True)[fpu_id][idx]
            ).as_scalar()
            print("%s limit hit at position %f" % (which_limit, limit_val))
        else:
            limit_val = NaN

        if test_valid:
            record = LimitTestResult(
                fpu_id=fpu_id,
                serialnumber=sn,
                result=TestResult.OK if test_succeeded else TestResult.FAILED,
                val=limit_val,
                diagnostic=diagnostic,
            )

            save_angular_limit(dbe, which_limit, record)

        if test_valid and test_succeeded and (which_limit != "beta_collision"):
            if rig.opts.verbosity > 0:
                print(
                    "FPU %i = %s: setting limit %s to %7.2f"
                    % (
                        fpu_id,
                        rig.fpu_config[fpu_id]["serialnumber"],
                        which_limit,
                        limit_val,
                    )
                )

            set_protection_limit(dbe, rig.grid_state, which_limit, record)

        if test_succeeded:
            # bring FPU back into valid range and protected state
            N = rig.opts.N
            if which_limit in ["alpha_max", "alpha_min"]:
                print("moving fpu %i back by %i degree" % (fpu_id, dw))
                rig.gd.resetFPUs(rig.grid_state, [fpu_id])
                wf = gen_wf(dw * dirac(fpu_id, N), 0)
                rig.gd.configMotion(
                    wf,
                    rig.grid_state,
                    soft_protection=False,
                    warn_unsafe=False,
                    allow_uninitialized=True,
                )
                rig.gd.executeMotion(rig.grid_state, fpuset=[fpu_id])
            else:
                print("moving fpu %i back by %i steps" % (fpu_id, 10))
                for k in range(3):
                    rig.gd.freeBetaCollision(
                        fpu_id, free_dir, rig.grid_state, soft_protection=False
                    )
                    rig.gd.pingFPUs(rig.grid_state, [fpu_id])
                rig.gd.enableBetaCollisionProtection(rig.grid_state)
                wf = gen_wf(0, dw * dirac(fpu_id, N))
                rig.gd.configMotion(
                    wf,
                    rig.grid_state,
                    soft_protection=False,
                    warn_unsafe=False,
                    allow_uninitialized=True,
                )
                rig.gd.executeMotion(rig.grid_state, fpuset=[fpu_id])

        # bring fpu back to default position
        goto_position(
            rig.gd,
            abs_alpha_def,
            abs_beta_def,
            rig.grid_state,
            fpuset=[fpu_id],
            allow_uninitialized=True,
            soft_protection=False,
        )
        print("searching datum for FPU %i, to resolve collision" % fpu_id)
        rig.gd.findDatum(rig.grid_state, fpuset=[fpu_id])

    if which_limit == "beta_collision":
        # home turntable
        rig.hw.safe_home_turntable(rig.gd, rig.grid_state)

    if failed_fpus:
        if which_limit == "beta_collision":
            raise CollisionDetectionFailure(
                "test of beta collision detection failed for FPUs %r" % failed_fpus
            )
        else:
            raise LimitDetectionFailure(
                "limit detection for %s failed for FPUs %r" % (which_limit, failed_fpus)
            )
