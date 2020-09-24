from __future__ import absolute_import, division, print_function

import logging
import warnings
from vfr.auditlog import get_fpuLogger
from fpu_constants import StepsPerDegreeBeta
from fpu_commands import gen_wf
from FpuGridDriver import (
    CAN_PROTOCOL_VERSION,
    DASEL_ALPHA,
    DASEL_BETA,
    DASEL_BOTH,
    DATUM_TIMEOUT_DISABLE,
    REQD_ANTI_CLOCKWISE,
    REQD_CLOCKWISE,
    SEARCH_CLOCKWISE,
    FirmwareTimeoutError,
    CollisionError,
    ConnectionFailure,
    InvalidStateException,
    LimitBreachError,
    MovementError,
)
from numpy import NaN, ceil, sign
from vfr.db.base import TestResult
from vfr.db.colldect_limits import (
    LimitTestResult,
    get_anglimit_passed_p,
    save_angular_limit,
    set_protection_limit,
)
from vfr.db.datum import save_datum_result
from vfr.tests_common import (
    dirac,
    flush,
    get_sorted_positions,
    goto_position,
    safe_home_turntable,
    turntable_safe_goto,
    check_for_quit,
    request_quit
)
from vfr.turntable import go_collision_test_pos

# calm down pyflakes static checker
assert DASEL_ALPHA or DASEL_BETA or True


class DatumFailure(Exception):
    pass


class CollisionDetectionFailure(Exception):
    pass


class LimitDetectionFailure(Exception):
    pass


def rewind_fpus(rig, abs_alpha, abs_beta):
    logger = logging.getLogger(__name__)
    # depending on options, we reset & rewind the FPUs
    if rig.opts.always_reset_fpus:
        logger.info("resetting FPUs.... ")
        flush()
        rig.gd.resetFPUs(rig.grid_state, fpuset=rig.measure_fpuset)
        logger.info("resetting FPUs.... OK")

    rig.gd.pingFPUs(rig.grid_state, fpuset=rig.measure_fpuset)

    check_for_quit()
    goto_position(
        rig.gd,
        abs_alpha,
        abs_beta,
        rig.grid_state,
        fpuset=rig.measure_fpuset,
        allow_uninitialized=True,
    )
    check_for_quit()


def test_datum(rig, dbe, dasel=DASEL_BOTH):

    check_for_quit()
    logger = logging.getLogger(__name__)

    failed_fpus = []

    if rig.opts.always_reset_fpus:
        logger.info("resetting FPUs.... ")
        rig.gd.resetFPUs(rig.grid_state, fpuset=rig.measure_fpuset)
        logger.info("resetting FPUs.... OK")

    rig.gd.pingFPUs(rig.grid_state, fpuset=rig.measure_fpuset)

    # Now, we issue a findDatum method. In order to know when and how
    # this command finished, we pass the rig.grid_state variable.

    modes = {fpu_id: SEARCH_CLOCKWISE for fpu_id in rig.measure_fpuset}
    logger.info("----------------------------------------")
    logger.info("datum functional test: issuing findDatum (%s):" % dasel)
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

    logger.info("findDatum finished, success=%s, rigstate=%s" % (success, rigstate))

    if valid:
        save_datum_result(rig, dbe, dasel, rigstate)

    for fpu_id, fpu in enumerate(rig.grid_state.FPU):
        if fpu_id not in rig.measure_fpuset:
            continue
        if not success:
            fpu_logger = get_fpuLogger(fpu_id, rig.fpu_config, __name__)
            serial_number = rig.fpu_config[fpu_id]["serialnumber"]
            fpu_logger.critical("Datum test failed for FPU %r" % serial_number)
            failed_fpus.append((fpu_id, serial_number))

    if failed_fpus:
        logger.critical("Datum test failed for FPUs %r" % failed_fpus)
        raise DatumFailure("Datum test failed for FPUs %r" % failed_fpus)
    check_for_quit()
    logger.info("datum functional test with dasel=%s finished successfully" % dasel)


def test_limit(rig, dbe, which_limit, pars=None):

    check_for_quit()
    assert (CAN_PROTOCOL_VERSION == 2), "This limit testing function only works with CAN protocol 2"

    logger = logging.getLogger(__name__)
    logger.info("----------------------------------------")
    logger.info("functional limit test for %s started" % which_limit)

    failed_fpus = []

    abs_alpha_def = -179.0
    abs_beta_def = 0.0
    goto_position(
        rig.gd, abs_alpha_def, abs_beta_def, rig.grid_state, fpuset=rig.measure_fpuset
    )

    if which_limit == "alpha_min":
        #print("Alpha min")
        abs_alpha, abs_beta = pars.LIMIT_ALPHA_NEG_EXPECT, 0.0
        free_dir = REQD_ANTI_CLOCKWISE
        dw = 30
        idx = 0
    elif which_limit == "alpha_max":
        #print("Alpha max")
        abs_alpha, abs_beta = pars.LIMIT_ALPHA_POS_EXPECT, 0.0
        free_dir = REQD_CLOCKWISE
        dw = -30
        idx = 0
    elif which_limit == "beta_min":
        #print("Beta min")
        abs_alpha, abs_beta = -180.0, pars.LIMIT_BETA_NEG_EXPECT
        free_dir = REQD_ANTI_CLOCKWISE
        dw = 30
        idx = 1
    elif which_limit == "beta_max":
        #print("Beta max")
        abs_alpha, abs_beta = -180.0, pars.LIMIT_BETA_POS_EXPECT
        free_dir = REQD_CLOCKWISE
        dw = -30
        idx = 1
    elif which_limit == "beta_collision":
        #print("Beta collision")
        abs_alpha, abs_beta = pars.COLDECT_ALPHA, pars.COLDECT_BETA
        free_dir = REQD_CLOCKWISE
        dw = -30
        idx = 1

    if which_limit != "beta_collision":
        # home turntable
        safe_home_turntable(rig, rig.grid_state)

    for fpu_id, stage_position in get_sorted_positions(
        rig.measure_fpuset, pars.COLDECT_POSITIONS
    ):
        sn = rig.fpu_config[fpu_id]["serialnumber"]
        fpu_logger = get_fpuLogger(fpu_id, rig.fpu_config, __name__)
        fpu_logger.info(
            "testing FPU %s for correct handling of limit %s" % (sn, which_limit)
        )

        check_for_quit()
        if (
            get_anglimit_passed_p(dbe, fpu_id, which_limit)
            and (
                (not rig.opts.repeat_passed_tests) and (which_limit != "beta_collision")
            )
            and (not rig.opts.repeat_limit_tests)
        ):

            fpu_logger.info(
                "FPU %s : limit test %r already passed, skipping test"
                % (sn, which_limit)
            )
            continue

        try:
            if which_limit == "beta_collision":
                # home turntable
                fpu_logger.info("pre-finding datum....")
                rig.gd.findDatum(rig.grid_state)
                fpu_logger.info("pre-finding datum.... OK")
                safe_home_turntable(rig, rig.grid_state, opts=rig.opts)
                # inform mocked hardware about place of collision it has to simulate
                go_collision_test_pos(fpu_id, rig.opts)

            fpu_logger.info(
                "limit test %s: provoking limit breach: moving fpu %i to position (%6.2f, %6.2f)"
                % (which_limit, fpu_id, abs_alpha, abs_beta)
            )

            if which_limit == "beta_collision":
                # move rotary stage to POS_REP_POSN_N
                turntable_safe_goto(rig, rig.grid_state, stage_position)

            msg_assurance = (
                "NOTE: FPU collision or limit breach error occuring"
                " next is intentional and part of test"
            )
            if which_limit == "beta_collision":
                goto_position(
                    rig.gd,
                    abs_alpha,
                    abs_beta - pars.COLDECT_BETA_SPAN,
                    rig.grid_state,
                    fpuset=[fpu_id],
                    soft_protection=False,
                )
                fpu_logger.info(msg_assurance)
                goto_position(
                    rig.gd,
                    abs_alpha,
                    abs_beta + pars.COLDECT_BETA_SPAN,
                    rig.grid_state,
                    fpuset=[fpu_id],
                    soft_protection=False,
                )

            else:
                fpu_logger.info(msg_assurance)
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
            logger.debug("detected : %s" % str(e))

        except MovementError as e:
            test_succeeded = False
            test_valid = False
            diagnostic = str(e)
            serial_number = rig.fpu_config[fpu_id]["serialnumber"]
            fpu_logger.critical(
                "FPU %s failed for limit test %r, diagnostic = %s"
                % (serial_number, which_limit, diagnostic)
            )
            failed_fpus.append((fpu_id, serial_number))

        fpu_logger.info(
            "FPU %i test result: valid=%s, succeeded=%r, diagnostic=%s"
            % (fpu_id, test_valid, test_succeeded, diagnostic)
        )

        if test_succeeded:
            # 2019-12-09: Query the limit location from the step count, not the tracked angles.
            rig.gd.pingFPUs(rig.grid_state, fpuset=[fpu_id])
            limit_val = rig.gd.countedAngles(rig.grid_state, show_uninitialized=True)[fpu_id][idx]
            #limit_val = (
            #    rig.gd.trackedAngles(rig.grid_state, retrieve=True)[fpu_id][idx]
            #).as_scalar()
            fpu_logger.info("%s limit hit at position %7.3f" % (which_limit, limit_val))
        else:
            limit_val = NaN
            if 'beta' in which_limit:
               # A beta limit failure or collision failure is now regarded as
               # a fatal, critical error (since further tests before the
               # collision protection circuit is checked could damage the FPU).
               logger.critical("Limit test %r failed for FPU %i. Quit requested!" % \
                   (which_limit, fpu_id))
               request_quit()

        if test_valid:
            record = LimitTestResult(
                fpu_id=fpu_id,
                serialnumber=sn,
                result=TestResult.OK if test_succeeded else TestResult.FAILED,
                val=limit_val,
                limit_name=which_limit,
                diagnostic=diagnostic,
            )

            save_angular_limit(dbe, which_limit, record)

        if test_valid and test_succeeded and (which_limit != "beta_collision"):
            fpu_logger.audit(
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
            #print( "FPU state:\n" + str(rig.grid_state.FPU[0]) )
            # bring FPU back into valid range and protected state
            N = rig.opts.N
            if which_limit in ["alpha_max", "alpha_min"]:
                n_steps = 10 * sign(int(dw))
                n_moves = 3

                # NOTE: This section converted to protocol 2.
                # resetFPUs replaced with freeAlphaLimitBreach followed by enableAlphaLimitprotection,
                # move to a safe location with software protection=False, then remove the second reset.
                for k in range(n_moves):
                    #print("freeAlphaLimitBreach: ", k)
                    rig.gd.freeAlphaLimitBreach(
                        fpu_id, free_dir, rig.grid_state, soft_protection=False
                    )
                    rig.gd.pingFPUs(rig.grid_state, [fpu_id])
                    angle = rig.gd.trackedAngles(rig.grid_state, retrieve=True)[fpu_id]
                    fpu_logger.trace(
                        "alpha limit recovery: fpu %i current angle = %s [%i}"
                        % (fpu_id, repr(angle), k)
                    )
                #print("enableAlphaLimitProtection")
                rig.gd.enableAlphaLimitProtection(rig.grid_state)
                #print( "FPU state:\n" + str(rig.grid_state.FPU[0]) )

                fpu_logger.debug("moving fpu %i back by %i degree" % (fpu_id, dw))
                #rig.gd.resetFPUs(rig.grid_state, [fpu_id])
                wf = gen_wf(dw * dirac(fpu_id, N), 0)
                rig.gd.configMotion(
                    wf,
                    rig.grid_state,
                    soft_protection=False,
                    warn_unsafe=False,
                    allow_uninitialized=True,
                )
                rig.gd.executeMotion(rig.grid_state, fpuset=[fpu_id])
                #print( "FPU state:\n" + str(rig.grid_state.FPU[0]) )
            else:
                fpu_logger.debug("moving fpu %i back by %i steps" % (fpu_id, 10))
                RECOVERY_STEPS_PER_ITERATION = 10
                recovery_steps = pars.RECOVERY_ANGLE_DEG * StepsPerDegreeBeta
                recovery_iterations = int(
                    ceil(recovery_steps / RECOVERY_STEPS_PER_ITERATION)
                )

                for k in range(recovery_iterations):
                    rig.gd.freeBetaCollision(
                        fpu_id, free_dir, rig.grid_state, soft_protection=False
                    )
                    rig.gd.pingFPUs(rig.grid_state, [fpu_id])
                    angle = rig.gd.trackedAngles(rig.grid_state, retrieve=True)[fpu_id]
                    #print("recovering FPU, current angle = %s" % repr(angle))
                    if (k % 8) == 0:
                        fpu_logger.debug(
                            "recovering FPU, current angle = %s" % repr(angle)
                        )

                #print("enableBetaCollisionProtection")
                rig.gd.enableBetaCollisionProtection(rig.grid_state)
                #print( "FPU state:\n" + str(rig.grid_state.FPU[0]) )

                logger.debug("Move FPU %d by alpha=%f, beta=%f" % (fpu_id, 0, dw)) 
                wf = gen_wf(0, dw * dirac(fpu_id, N))
                rig.gd.configMotion(
                    wf,
                    rig.grid_state,
                    soft_protection=False,
                    warn_unsafe=False,
                    allow_uninitialized=True,
                )
                rig.gd.executeMotion(rig.grid_state, fpuset=[fpu_id])
                #print( "FPU state:\n" + str(rig.grid_state.FPU[0]) )

        # bring fpu back to default position
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            goto_position(
                rig.gd,
                abs_alpha_def,
                abs_beta_def,
                rig.grid_state,
                fpuset=[fpu_id],
                allow_uninitialized=True,
                soft_protection=False,
            )
        fpu_logger.debug("Searching datum for FPU %i, to resolve collision" % fpu_id)
        rig.gd.findDatum(rig.grid_state, fpuset=[fpu_id])
        check_for_quit()

    if which_limit == "beta_collision":
        # home turntable
        safe_home_turntable(rig, rig.grid_state)

    if failed_fpus:
        logger.critical("Limit test %r failed for FPUs %r" % (which_limit, failed_fpus))
        if which_limit == "beta_collision":
            raise CollisionDetectionFailure(
                "Test of beta collision detection failed for FPUs %r" % failed_fpus
            )
        else:
            raise LimitDetectionFailure(
                "limit detection for %s failed for FPUs %r" % (which_limit, failed_fpus)
            )
    logger.info("functional limit test for %s successfully passed" % which_limit)
