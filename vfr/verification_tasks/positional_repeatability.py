from __future__ import absolute_import, division, print_function

import warnings

from fpu_commands import gen_wf
from Gearbox.gear_correction import GearboxFitError, fit_gearbox_correction
from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.analyze_positional_repeatability import (
    POSITIONAL_REPEATABILITY_ALGORITHM_VERSION,
    ImageAnalysisError,
    evaluate_positional_repeatability,
    posrepCoordinates,
)
from numpy import NaN
from vfr import hw, hwsimulation
from vfr.conf import POS_REP_CAMERA_IP_ADDRESS
from vfr.db.colldect_limits import get_anglimit_passed_p, get_angular_limit
from vfr.db.positional_repeatability import (
    TestResult,
    get_positional_repeatability_images,
    get_positional_repeatability_passed_p,
    get_positional_repeatability_result,
    save_positional_repeatability_images,
    save_positional_repeatability_result,
)
from vfr.db.pupil_alignment import get_pupil_alignment_passed_p
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


def measure_positional_repeatability(ctx, pars=None):

    tstamp = timestamp()
    if ctx.opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    # home turntable
    hw.safe_home_turntable(ctx.gd, ctx.grid_state)

    ctx.lctrl.switch_fibre_backlight("off", manual_lamp_control=ctx.opts.manual_lamp_control)
    ctx.lctrl.switch_fibre_backlight_voltage(
        0.0, manual_lamp_control=ctx.opts.manual_lamp_control
    )

    with ctx.lctrl.use_ambientlight(manual_lamp_control=ctx.opts.manual_lamp_control):
        # initialize pos_rep camera
        # set pos_rep camera exposure time to POSITIONAL_REP_EXPOSURE milliseconds
        POS_REP_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: POS_REP_CAMERA_IP_ADDRESS,
        }

        pos_rep_cam = hw.GigECamera(POS_REP_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(pars.POS_REP_EXPOSURE_MS)

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(
            ctx.eval_fpuset, pars.POS_REP_POSITIONS
        ):

            sn = ctx.fpu_config[fpu_id]["serialnumber"]
            if not get_datum_repeatability_passed_p(ctx, fpu_id):
                print(
                    "FPU %s: skipping positional repeatability measurement because"
                    " there is no passed datum repeatability test" % sn
                )
                continue

            if not get_pupil_alignment_passed_p(ctx, fpu_id):
                if ctx.opts.skip_fibre:
                    warnings.warn(
                        "skipping check for pupil alignment because '--skip-fibre' flag is set"
                    )
                else:
                    print(
                        "FPU %s: skipping positional repeatability measurement because"
                        " there is no passed pupil alignment test"
                        " (use '--skip-fibre' flag if you want to omit that test)" % sn
                    )
                    continue

            if get_positional_repeatability_passed_p(ctx, fpu_id) and (
                not ctx.opts.repeat_passed_tests
            ):

                print(
                    "FPU %s : positional repeatability test already passed, skipping test"
                    % sn
                )
                continue

            alpha_min = get_angular_limit(ctx, fpu_id, "alpha_min")["val"]
            alpha_max = get_angular_limit(ctx, fpu_id, "alpha_max")["val"]
            beta_min = get_angular_limit(ctx, fpu_id, "beta_min")["val"]
            beta_max = get_angular_limit(ctx, fpu_id, "beta_max")["val"]

            if (
                (alpha_min is None)
                or (alpha_max is None)
                or (beta_min is None)
                or (beta_max is None)
            ):
                print("FPU %s : limit test value missing, skipping test" % sn)
                continue

            # move rotary stage to POS_REP_POSN_N
            hw.turntable_safe_goto(ctx.gd, ctx.grid_state, stage_position)

            image_dict_alpha = {}
            image_dict_beta = {}

            def capture_image(iteration, increment, direction, alpha, beta):

                ipath = store_image(
                    pos_rep_cam,
                    "{sn}/{tn}/{ts}/{itr:03d}-{inc:03d}-{dir:03d}-({alpha:+08.3f},_{beta:+08.3f}).bmp",
                    sn=sn,
                    tn="positional-repeatability",
                    ts=tstamp,
                    itr=iteration,
                    inc=increment,
                    dir=direction,
                    alpha=alpha,
                    beta=beta,
                )

                return ipath

            for i in range(pars.POS_REP_ITERATIONS):
                find_datum(ctx.gd, ctx.grid_state, opts=ctx.opts)

                step_a = (
                    alpha_max - alpha_min - 2 * pars.POS_REP_SAFETY_MARGIN
                ) / pars.POS_REP_NUM_INCREMENTS
                step_b = (
                    beta_max - beta_min - 2 * pars.POS_REP_SAFETY_MARGIN
                ) / pars.POS_REP_NUM_INCREMENTS

                alpha0 = alpha_min + pars.POS_REP_SAFETY_MARGIN
                beta0 = beta_min + pars.POS_REP_SAFETY_MARGIN

                for j in range(4):

                    M = pars.POS_REP_NUM_INCREMENTS
                    for k in range(M):
                        if j == 0:
                            ka = k
                            kb = 0
                        elif j == 1:
                            ka = M - k - 1
                            kb = 0
                        elif j == 2:
                            ka = 0
                            kb = k
                        elif j == 3:
                            ka = 0
                            kb = M - k - 1

                        abs_alpha = alpha0 + step_a * ka
                        abs_beta = beta0 + step_b * kb

                        if ctx.opts.verbosity > 1:
                            print(
                                "FPU %s measurement [%2i, %2i, %2i]: going to position (%7.2f, %7.2f)"
                                % (sn, i, j, k, abs_alpha, abs_beta)
                            )

                        goto_position(
                            ctx.gd, abs_alpha, abs_beta, ctx.grid_state, fpuset=[fpu_id]
                        )

                        # to get the angles, we need to pass all connected FPUs
                        fpuset = range(ctx.opts.N)
                        angles = ctx.gd.countedAngles(ctx.grid_state, fpuset=fpuset)

                        alpha_count = angles[fpu_id][0]
                        beta_count = angles[fpu_id][1]

                        alpha_steps = ctx.grid_state.FPU[fpu_id].alpha_steps
                        beta_steps = ctx.grid_state.FPU[fpu_id].beta_steps

                        ipath = capture_image(i, j, k, alpha_count, beta_count)
                        if j in [0, 1]:
                            image_dict_alpha[(abs_alpha, abs_beta, i, j, k)] = (
                                alpha_steps,
                                beta_steps,
                                ipath,
                            )
                        else:
                            image_dict_beta[(abs_alpha, abs_beta, i, j, k)] = (
                                alpha_steps,
                                beta_steps,
                                ipath,
                            )

            save_positional_repeatability_images(
                ctx,
                fpu_id,
                image_dict_alpha=image_dict_alpha,
                image_dict_beta=image_dict_beta,
                waveform_pars=pars.POS_REP_WAVEFORM_PARS,
            )


def eval_positional_repeatability(ctx, pos_rep_analysis_pars, pos_rep_evaluation_pars):
    def analysis_func(ipath):
        return posrepCoordinates(ipath, pars=pos_rep_analysis_pars)

    for fpu_id in ctx.eval_fpuset:
        measurement = get_positional_repeatability_images(ctx, fpu_id)

        if measurement is None:
            print("FPU %s: no positional repeatability measurement data found" % fpu_id)
            continue

        images_alpha = measurement["images_alpha"]
        images_beta = measurement["images_beta"]

        try:
            analysis_results_alpha = {}
            analysis_results_alpha_short = {}

            for k, v in images_alpha.items():
                alpha_steps, beta_steps, ipath = v
                analysis_results_alpha[k] = analysis_func(ipath)
                (
                    x_measured_small,
                    y_measured_small,
                    qual_small,
                    x_measured_big,
                    y_measured_big,
                    qual_big,
                ) = analysis_results_alpha[k]

                analysis_results_alpha_short[k] = (
                    x_measured_small,
                    y_measured_small,
                    x_measured_big,
                    y_measured_big,
                )
            analysis_results_beta = {}
            analysis_results_beta_short = {}

            for k, v in images_beta.items():
                alpha_steps, beta_steps, ipath = v
                analysis_results_beta[k] = analysis_func(ipath)
                (
                    x_measured_small,
                    y_measured_small,
                    qual_small,
                    x_measured_big,
                    y_measured_big,
                    qual_big,
                ) = analysis_results_beta[k]

                analysis_results_beta_short[k] = (
                    x_measured_small,
                    y_measured_small,
                    x_measured_big,
                    y_measured_big,
                )

                (
                    posrep_alpha_max_at_angle,
                    posrep_beta_max_at_angle,
                    posrep_alpha_max,
                    posrep_beta_max,
                    posrep_rss_mm,
                ) = evaluate_positional_repeatability(
                    analysis_results_alpha_short,
                    analysis_results_beta_short,
                    pars=pos_rep_evaluation_pars,
                )

            positional_repeatability_has_passed = (
                TestResult.OK
                if posrep_rss_mm <= pos_rep_evaluation_pars.POS_REP_PASS
                else TestResult.FAILED
            )

            gearbox_correction = fit_gearbox_correction(
                analysis_results_alpha_short, analysis_results_beta_short
            )
            errmsg = ""

        except (ImageAnalysisError, GearboxFitError) as e:
            analysis_results = None
            errmsg = str(e)
            posrep_alpha_max_at_angle = (NaN,)
            posrep_beta_max_at_angle = (NaN,)
            posrep_alpha_max = (NaN,)
            posrep_beta_max = (NaN,)
            posrep_rss_mm = (NaN,)
            positional_repeatability_has_passed = TestResult.NA

        save_positional_repeatability_result(
            ctx,
            fpu_id,
            pos_rep_calibration_pars=pos_rep_analysis_pars.POS_REP_CALIBRATION_PARS,
            analysis_results_alpha=analysis_results_alpha,
            analysis_results_beta=analysis_results_beta,
            posrep_alpha_max_at_angle=posrep_alpha_max_at_angle,
            posrep_beta_max_at_angle=posrep_beta_max_at_angle,
            posrep_alpha_max=posrep_alpha_max,
            posrep_beta_max=posrep_beta_max,
            posrep_rss_mm=posrep_rss_mm,
            positional_repeatability_has_passed=positional_repeatability_has_passed,
            pass_threshold=pos_rep_evaluation_pars.POS_REP_PASS,
            gearbox_correction=gearbox_correction,
            errmsg=errmsg,
            analysis_version=POSITIONAL_REPEATABILITY_ALGORITHM_VERSION,
        )
