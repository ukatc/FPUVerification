from __future__ import absolute_import, division, print_function

import warnings
import random

from fpu_commands import gen_wf
from Gearbox.gear_correction import (
    GearboxFitError,
    apply_gearbox_correction,
    fit_gearbox_correction,
)
from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.analyze_positional_repeatability import (
    POSITIONAL_REPEATABILITY_ALGORITHM_VERSION,
    POSITIONAL_VERIFICATION_ALGORITHM_VERSION,
    ImageAnalysisError,
    evaluate_positional_verification,
    posrepCoordinates,
)
from numpy import NaN
from vfr import hw, hwsimulation
from vfr.conf import POS_REP_CAMERA_IP_ADDRESS
from vfr.db.colldect_limits import get_angular_limit, get_anglimit_passed_p
from vfr.db.datum_repeatability import get_datum_repeatability_passed_p
from vfr.db.positional_repeatability import (
    TestResult,
    get_positional_repeatability_passed_p,
    get_positional_repeatability_result,
)
from vfr.db.positional_verification import (
    TestResult,
    get_positional_verification_images,
    get_positional_verification_passed_p,
    save_positional_verification_images,
    save_positional_verification_result,
)
from vfr.db.pupil_alignment import get_pupil_alignment_passed_p
from vfr.tests_common import (
    dirac,
    find_datum,
    flush,
    get_stepcounts,
    get_sorted_positions,
    goto_position,
    store_image,
    timestamp,
)
from vfr.verification_tasks.measure_datum_repeatability import (
    get_datum_repeatability_passed_p,
)
from vfr.verification_tasks.positional_repeatability import (
    POSITIONAL_REPEATABILITY_ALGORITHM_VERSION,
    get_positional_repeatability_passed_p,
    get_positional_repeatability_result,
)


def generate_tested_positions(
    niterations, alpha_min=NaN, alpha_max=NaN, beta_min=NaN, beta_max=NaN
):
    positions = []

    N_FIX_POS=8
    for k in range(N_FIX_POS):
        positions.append(
            (alpha_min + k * (alpha_max - alpha_min) / float(N_FIX_POS),
             beta_min + 10)
        )

    interval_alpha = (alpha_max - alpha_min) / float(niterations)
    interval_beta = (beta_max - beta_min) / float(niterations)
    ralpha = range(niterations)
    rbeta = range(niterations)
    random.shuffle(ralpha)
    random.shuffle(rbeta)
    for ra, rb in zip(ralpha, rbeta):
        alpha_start = alpha_min + ra * interval_alpha
        beta_start = beta_min + rb * interval_beta
        alpha = random.uniform(alpha_start, alpha_start + interval_alpha)
        beta = random.uniform(beta_start, beta_start + interval_beta)
        positions.append((alpha, beta))

    return positions


def measure_positional_verification(ctx, pars=None):

    # home turntable
    tstamp = timestamp()

    opts = ctx.opts
    gd = ctx.gd
    grid_state = ctx.grid_state

    if opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    hw.safe_home_turntable(gd, grid_state)

    hw.switch_fibre_backlight("off", manual_lamp_control=opts.manual_lamp_control)
    hw.switch_ambientlight("on", manual_lamp_control=opts.manual_lamp_control)
    hw.switch_fibre_backlight_voltage(0.0, manual_lamp_control=opts.manual_lamp_control)

    with hw.use_ambientlight(manual_lamp_control=opts.manual_lamp_control):
        # initialize pos_rep camera
        # set pos_rep camera exposure time to POS_VER_EXPOSURE milliseconds
        POS_VER_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: POS_REP_CAMERA_IP_ADDRESS,
        }

        pos_rep_cam = hw.GigECamera(POS_VER_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(pars.POS_VER_EXPOSURE_MS)

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(
            ctx.measure_fpuset, pars.POS_REP_POSITIONS
        ):

            sn = ctx.fpu_config[fpu_id]["serialnumber"]
            if not get_datum_repeatability_passed_p(ctx, fpu_id):
                print(
                    "FPU %s: skipping positional verification measurement because"
                    " there is no passed datum verification test" % sn
                )
                continue

            if get_pupil_alignment_passed_p(ctx, fpu_id):
                if opts.skip_fibre:
                    print(
                        "FPU %s: ignoring missing pupil alignment test,\n"
                        " because '--skip-fibre' option is set." % sn
                    )
                else:
                    print(
                        "FPU %s: skipping positional verification measurement,\n"
                        "because there is no passed pupil alignment test \n"
                        "(set option '--skip-fibre' to ignore missing test)" % sn
                    )
                continue

            if not get_positional_repeatability_passed_p(ctx, fpu_id):
                print(
                    "FPU %s: skipping positional verification measurement because"
                    " there is no passed positional repeatability test" % sn
                )
                continue

            if get_positional_verification_passed_p(ctx, fpu_id) and (
                not opts.repeat_passed_tests
            ):

                print(
                    "FPU %s : positional verification test already passed,"
                    "and flag '--repeat-passed-tests' not set, skipping test" % sn
                )
                continue

            alpha_min = get_angular_limit(ctx, fpu_id, "alpha_min")["val"]
            alpha_max = get_angular_limit(ctx, fpu_id, "alpha_max")["val"]
            beta_min = get_angular_limit(ctx, fpu_id, "beta_min")["val"]
            beta_max = get_angular_limit(ctx, fpu_id, "beta_max")["val"]

            if opts.verbosity > 0:
                print("FPU %s: limits: alpha = %7.2f .. %7.2f" % (sn, alpha_min, alpha_max))
                print("FPU %s: limits: beta = %7.2f .. %7.2f" % (sn, beta_min, beta_max))

            if (alpha_min and alpha_max and beta_min and beta_max) is None:
                print(
                    "FPU %s : positional verification test skipped, range limits missing"
                    % sn
                )
                continue

            pr_result = get_positional_repeatability_result(ctx, fpu_id)
            if (
                pr_result["algorithm_version"]
                < POSITIONAL_REPEATABILITY_ALGORITHM_VERSION
            ):
                warnings.warn(
                    "FPU %s: positional repeatability data uses old version of image analysis"
                    % sn
                )

            gearbox_correction = pr_result["gearbox_correction"]
            fpu_coeffs = gearbox_correction["coeffs"]

            # move rotary stage to POS_VER_POSN_N
            hw.turntable_safe_goto(gd, grid_state, stage_position)

            image_dict = {}

            def capture_image(idx, alpha, beta):

                ipath = store_image(
                    pos_rep_cam,
                    "{sn}/{tn}/{ts}/{idx:04d}-{alpha:+08.3f}-{beta:+08.3f}.bmp",
                    sn=sn,
                    tn="positional-verification",
                    alpha=alpha,
                    beta=beta,
                    ts=tstamp,
                    idx=idx,
                )

                return ipath

            tol = abs(pars.POS_VER_SAFETY_TOLERANCE)
            tested_positions = generate_tested_positions(
                pars.POS_VER_ITERATIONS,
                alpha_min=alpha_min + tol,
                alpha_max=alpha_max - tol,
                beta_min=beta_min + tol,
                beta_max=beta_max - tol,
            )

            find_datum(gd, grid_state, opts)

            image_dict = {}
            for k, (alpha, beta) in enumerate(tested_positions):
                # get current step count
                alpha_cursteps, beta_cursteps = get_stepcounts(gd, grid_state, fpu_id)

                # get absolute corrected step count from desired absolute angle
                asteps_target, bsteps_target = apply_gearbox_correction(
                    (alpha, beta), coeffs=fpu_coeffs
                )

                verbosity = opts.verbosity

                if verbosity > 0:
                    print(
                        "FPU %s: measurement #%i - moving to (%7.2f, %7.2f) degrees = (%i, %i) steps"
                        % (sn, k, alpha, beta, asteps_target, bsteps_target)
                    )

                # compute deltas of step counts
                adelta = asteps_target - alpha_cursteps
                bdelta = bsteps_target - beta_cursteps

                N = opts.N
                # move by delta
                wf = gen_wf(
                    dirac(fpu_id, N) * adelta, dirac(fpu_id, N) * bdelta, units="steps"
                )

                verbosity_ = max(verbosity - 3, 0)

                gd.configMotion(wf, grid_state, verbosity=verbosity_)
                gd.executeMotion(grid_state)

                gd.pingFPUs(grid_state)
                alpha_actualsteps, beta_actualsteps = get_stepcounts(gd, grid_state, fpu_id)

                assert (
                    (alpha_actualsteps == asteps_target) and (beta_actualsteps == bsteps_target)
                ), "could not reach corrected step count"

                if verbosity > 0:
                    print("FPU %s: saving image # %i..." % (sn, k))

                ipath = capture_image(k, alpha, beta)

                image_dict[(k, alpha, beta)] = ipath

            # store dict of image paths
            save_positional_verification_images(ctx, fpu_id, image_dict=image_dict, gearbox_correction=gearbox_correction)


def eval_positional_verification(ctx, pos_ver_analysis_pars, pos_ver_evaluation_pars):
    def analysis_func(ipath):
        return posrepCoordinates(ipath, pars=pos_ver_analysis_pars)

    for fpu_id in ctx.eval_fpuset:
        measurement = get_positional_verification_images(ctx, fpu_id)

        if measurement is None:
            print("FPU %s: no positional verification measurement data found" % fpu_id)
            continue

        images = measurement["images"]

        try:
            analysis_results = {}
            analysis_results_short = {}

            for k, v in images.items():
                alpha_steps, beta_steps, count = k
                ipath = v
                analysis_results[k] = analysis_func(ipath)

                (
                    x_measured_small,
                    y_measured_small,
                    qual_small,
                    x_measured_big,
                    y_measured_big,
                    qual_big,
                ) = analysis_results[k]

                analysis_results_short[k] = (
                    x_measured_small,
                    y_measured_small,
                    x_measured_big,
                    y_measured_big,
                )

                (posver_error, posver_error_max) = evaluate_positional_verification(
                    analysis_results_short, pars=pos_ver_evaluation_pars
                )

            positional_verification_has_passed = (
                posver_error_max <= pos_ver_evaluation_pars.POS_VER_PASS
            )

            errmsg = ""

        except (ImageAnalysisError, GearboxFitError) as e:
            analysis_results = None
            errmsg = str(e)
            posver_error = ([],)
            posver_error_max = (NaN,)
            positional_verification_has_passed = TestResult.NA

        save_positional_verification_result(
            ctx,
            fpu_id,
            pos_ver_calibration_pars=pos_ver_analysis_pars.POS_REP_CALIBRATION_PARS,
            analysis_results=analysis_results,
            posver_error=posver_error,
            posver_error_max=posver_error_max,
            errmsg=errmsg,
            analysis_version=POSITIONAL_REPEATABILITY_ALGORITHM_VERSION,
            positional_verification_has_passed=positional_verification_has_passed,
            pass_threshold=pos_ver_evaluation_pars.POS_VER_PASS,
        )
