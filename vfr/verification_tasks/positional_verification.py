from __future__ import absolute_import, division, print_function

import warnings

from fpu_commands import gen_wf
from Gearbox.gear_correction import GearboxFitError, apply_gearbox_correction
from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.analyze_positional_repeatability import (
    POSITIONAL_VERIFICATION_ALGORITHM_VERSION,
    ImageAnalysisError,
    evaluate_positional_verification,
    fit_gearbox_correction,
    posrepCoordinates,
)
from numpy import NaN
from vfr import hw, hwsimulation
from vfr.conf import POS_REP_CAMERA_IP_ADDRESS
from vfr.db.positional_verification import (
    TestResult,
    get_positional_verification_images,
    save_positional_verification_images,
    save_positional_verification_result,
)
from vfr.tests_common import (
    dirac,
    find_datum,
    flush,
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

    for k in range(8):
        positions.append((10.0 + k * 45.0, -170.0))
    for r in range(niterations):
        alpha = random.uniform(alpha_min, alpha_max)
        beta = random.uniform(beta_min, beta_max)
        positions.append((alpha, beta))

    return positions


def measure_positional_verification(ctx, pars=None):

    # home turntable
    tstamp = timestamp()

    if ctx.opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    hw.safe_home_turntable(ctx.gd, grid_state)

    hw.switch_fibre_backlight("off", manual_lamp_control=ctx.opts.manual_lamp_control)
    hw.switch_ambientlight("on", manual_lamp_control=ctx.opts.manual_lamp_control)
    hw.switch_fibre_backlight_voltage(
        0.0, manual_lamp_control=ctx.opts.manual_lamp_control
    )

    with hw.use_ambientlight(manual_lamp_control=ctx.opts.manual_lamp_control):
        # initialize pos_rep camera
        # set pos_rep camera exposure time to POSITIONAL_VER_EXPOSURE milliseconds
        POS_VER_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: POS_REP_CAMERA_IP_ADDRESS,
        }

        pos_rep_cam = hw.GigECamera(POS_VER_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(pars.POSITIONAL_VER_EXPOSURE_MS)

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(
            ctx.measure_fpuset, pars.POS_REP_POSITIONS
        ):

            if not get_datum_verification_passed_p(ctx, fpu_id):
                print(
                    "FPU %s: skipping positional verification measurement because"
                    " there is no passed datum verification test"
                    % fpu_config["serialnumber"]
                )
                continue

            if not get_pupil_alignment_passed_p(ctx, fpu_id):
                print(
                    "FPU %s: skipping positional verification measurement because"
                    " there is no passed pupil alignment test"
                    % fpu_config["serialnumber"]
                )
                continue

            if not get_positional_repeatability_passed_p(ctx, fpu_id):
                print(
                    "FPU %s: skipping positional verification measurement because"
                    " there is no passed positional repeatability test"
                    % fpu_config["serialnumber"]
                )
                continue

            if get_datum_verification_passed_p(ctx, fpu_id) and (
                not ctx.opts.repeat_passed_tests
            ):

                sn = ctx.fpu_config[fpu_id]["serialnumber"]
                print(
                    "FPU %s : datum verification test already passed, skipping test"
                    % sn
                )
                continue

            alpha_min = get_angular_limit(ctx, fpu_id, sn, "alpha_min")
            alpha_max = get_angular_limit(ctx, fpu_id, sn, "alpha_max")
            beta_min = get_angular_limit(ctx, fpu_id, sn, "beta_min")
            beta_max = get_angular_limit(ctx, fpu_id, sn, "beta_max")

            pr_result = get_positional_repeatability_result(ctx, fpu_id)
            if (
                pr_result["analysis_version"]
                < POSITIONAL_REPEATABILITY_ALGORITHM_VERSION
            ):
                warnings.warn(
                    "FPU %s: positional repeatability data uses old version of image analysis"
                    % sn
                )

            gearbox_correction = pr_result["gearbox_correction"]
            fpu_coeffs = gearbox_correction["coeffs"]

            # move rotary stage to POS_VER_POSN_N
            hw.turntable_safe_goto(ctx.gd, grid_state, stage_position)

            image_dict = {}

            def capture_image(idx, alpha, beta):

                ipath = store_image(
                    pos_rep_cam,
                    "{sn}/{tn}/{ts}/{idx:04d}-{alpha:+08.3f}-{beta:+08.3f}.bmp",
                    sn=ctx.fpu_config[fpu_id]["serialnumber"],
                    tn="positional-verification",
                    alpha=alpha,
                    beta=beta,
                    ts=tstamp,
                    idx=dx,
                )

                return ipath

            tested_positions = generate_tested_positions(
                POSITIONAL_VER_ITERATIONS,
                alpha_min=alpha_min,
                alpha_max=alpha_max,
                beta_min=beta_min,
                beta_max=beta_max,
            )

            ctx.gd.findDatum(grid_state, fpuset=[fpu_id])

            image_dict = {}
            for k, (alpha, beta) in enumerate(tested_positions):
                # get current step count
                alpha_cursteps = ctx.grid_state.FPU[fpu_id].alpha_steps
                beta_cursteps = ctx.grid_state.FPU[fpu_id].beta_steps

                # get absolute corrected step count from desired absolute angle
                asteps_target, bsteps_target = apply_gearbox_correction(
                    (alpha, beta), coeffs=fpu_coeffs
                )

                # compute deltas of step counts
                adelta = asteps_target - alpha_cursteps
                bdelta = bsteps_target - beta_cursteps

                # move by delta
                wf = gen_wf(
                    dirac(fpu_id) * adelta, dirac(fpu_id) * bdelta, units="steps"
                )

                ctx.gd.configMotion(wf, ctx.grid_state)
                ctx.gd.executeMotion(ctx.grid_state)

                ipath = capture_image(k, alpha, beta)

                image_dict[(k, alpha, beta)] = ipath

            # store dict of image paths
            save_positional_verification_images(ctx, fpu_id, image_dict)


def eval_positional_verification(ctx, pos_rep_analysis_pars, pos_ver_evaluation_pars):
    def analysis_func(ipath):
        return positional_repeatability_image_analysis(
            ipath, pars=pos_rep_analysis_pars
        )

    for fpu_id in fpuset:
        image_dict = get_positional_verification_images(ctx, fpu_id)

        try:
            analysis_results_short = {}
            analysis_results = {}

            for k, v in images.items():
                analysis_results[k] = analysis_func(v)
                (
                    x_measured_1,
                    y_measured_1,
                    qual1,
                    x_measured_2,
                    y_measured_2,
                    qual2,
                ) = analysis_results[k]
                analysis_results_short[k] = (
                    x_measured_1,
                    y_measured_1,
                    x_measured_2,
                    y_measured_2,
                )

            posver_errors, positional_verification_mm = evaluate_positional_verification(
                analysis_results_short, **pos_ver_evaluation_pars
            )

            positional_verification_has_passed = (
                TestResult.OK
                if positional_verification_mm <= POSITIONAL_VER_PASS
                else TestResult.FAILED
            )

        except ImageAnalysisError as e:
            analysis_results = None
            errmsg = str(e)
            posver_errors = None
            positional_verification_mm = NaN
            positional_verification_has_passed = TestResult.NA

        save_positional_verification_result(
            ctx,
            fpu_id,
            analysis_results=analysis_results,
            posver_errors=posver_errors,
            positional_verification_mm=positional_verification_mm,
            positional_verification_has_passed=positional_verification_has_passed,
            ermmsg=errmsg,
            analysis_version=POSITIONAL_VERIFICATION_ALGORITHM_VERSION,
        )
