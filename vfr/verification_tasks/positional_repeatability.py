from __future__ import absolute_import, division, print_function

import warnings

from Gearbox.gear_correction import GearboxFitError, fit_gearbox_correction
from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.base import get_min_quality, arg_max_dict
from ImageAnalysisFuncs.analyze_positional_repeatability import (
    POSITIONAL_REPEATABILITY_ALGORITHM_VERSION,
    ImageAnalysisError,
    evaluate_positional_repeatability,
    posrepCoordinates,
)
from numpy import NaN
from fpu_constants import ALPHA_DATUM_OFFSET
from vfr.conf import POS_REP_CAMERA_IP_ADDRESS
from vfr.db.base import TestResult
from vfr.db.colldect_limits import get_angular_limit
from vfr.db.positional_repeatability import (
    PositionalRepeatabilityImages,
    PositionalRepeatabilityResults,
    get_positional_repeatability_images,
    get_positional_repeatability_passed_p,
    save_positional_repeatability_images,
    save_positional_repeatability_result,
)
from vfr.db.pupil_alignment import get_pupil_alignment_passed_p
from vfr.tests_common import (
    find_datum,
    get_sorted_positions,
    goto_position,
    store_image,
    timestamp,
)
from vfr.verification_tasks.measure_datum_repeatability import (
    get_datum_repeatability_passed_p,
)


def measure_positional_repeatability(rig, dbe, pars=None):

    tstamp = timestamp()

    # home turntable
    rig.hw.safe_home_turntable(rig.gd, rig.grid_state)

    rig.lctrl.switch_fibre_backlight("off")
    rig.lctrl.switch_fibre_backlight_voltage(0.0)

    with rig.lctrl.use_ambientlight():
        # initialize pos_rep camera
        # set pos_rep camera exposure time to POSITIONAL_REP_EXPOSURE milliseconds
        POS_REP_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: POS_REP_CAMERA_IP_ADDRESS,
        }

        pos_rep_cam = rig.hw.GigECamera(POS_REP_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(pars.POS_REP_EXPOSURE_MS)

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(
            rig.measure_fpuset, pars.POS_REP_POSITIONS
        ):

            sn = rig.fpu_config[fpu_id]["serialnumber"]
            if not get_datum_repeatability_passed_p(dbe, fpu_id):
                print(
                    "FPU %s: skipping positional repeatability measurement because"
                    " there is no passed datum repeatability test" % sn
                )
                continue

            if not get_pupil_alignment_passed_p(dbe, fpu_id):
                if rig.opts.skip_fibre:
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

            if get_positional_repeatability_passed_p(dbe, fpu_id) and (
                not rig.opts.repeat_passed_tests
            ):

                print(
                    "FPU %s : positional repeatability test already passed, skipping test"
                    % sn
                )
                continue

            _alpha_min = get_angular_limit(dbe, fpu_id, "alpha_min")
            if _alpha_min is None:
                _alpha_min = {"val" : ALPHA_DATUM_OFFSET}
            _alpha_max = get_angular_limit(dbe, fpu_id, "alpha_max")
            _beta_min = get_angular_limit(dbe, fpu_id, "beta_min")
            _beta_max = get_angular_limit(dbe, fpu_id, "beta_max")

            if (
                (_alpha_min is None)
                or (_alpha_max is None)
                or (_beta_min is None)
                or (_beta_max is None)
            ):
                print("FPU %s : limit test value missing, skipping test" % sn)
                continue

            alpha_min = _alpha_min["val"]
            alpha_max = _alpha_max["val"]
            beta_min = _beta_min["val"]
            beta_max = _beta_max["val"]

            # move rotary stage to POS_REP_POSN_N
            rig.hw.turntable_safe_goto(rig.gd, rig.grid_state, stage_position)

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
                find_datum(rig.gd, rig.grid_state, opts=rig.opts)

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

                        if rig.opts.verbosity > 0:
                            print(
                                "FPU %s measurement [%2i, %2i, %2i]: going to position (%7.2f, %7.2f)"
                                % (sn, i, j, k, abs_alpha, abs_beta)
                            )

                        goto_position(
                            rig.gd, abs_alpha, abs_beta, rig.grid_state, fpuset=[fpu_id]
                        )

                        # to get the angles, we need to pass all connected FPUs
                        fpuset = range(rig.opts.N)
                        angles = rig.gd.countedAngles(rig.grid_state, fpuset=fpuset)

                        alpha_count = angles[fpu_id][0]
                        beta_count = angles[fpu_id][1]

                        alpha_steps = rig.grid_state.FPU[fpu_id].alpha_steps
                        beta_steps = rig.grid_state.FPU[fpu_id].beta_steps

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

            record = PositionalRepeatabilityImages(
                images_alpha=image_dict_alpha,
                images_beta=image_dict_beta,
                waveform_pars=pars.POS_REP_WAVEFORM_PARS,
            )

            save_positional_repeatability_images(dbe, fpu_id, record)


def eval_positional_repeatability(dbe, pos_rep_analysis_pars, pos_rep_evaluation_pars):
    def analysis_func(ipath):
        return posrepCoordinates(ipath, pars=pos_rep_analysis_pars)

    for fpu_id in dbe.eval_fpuset:
        measurement = get_positional_repeatability_images(dbe, fpu_id)

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
                    posrep_alpha_max_mm,
                    posrep_beta_max_mm,
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

            alpha_coords = list(analysis_results_alpha.values())
            min_quality_alpha = get_min_quality(alpha_coords)

            beta_coords = list(analysis_results_beta.values())
            min_quality_beta = get_min_quality(beta_coords)

            arg_max_alpha_error, _ = arg_max_dict(posrep_alpha_max_at_angle)
            arg_max_beta_error, _ = arg_max_dict(posrep_beta_max_at_angle)

        except (ImageAnalysisError, GearboxFitError) as e:
            errmsg = str(e)
            posrep_alpha_max_at_angle = (NaN,)
            posrep_beta_max_at_angle = (NaN,)
            posrep_alpha_max_mm = (NaN,)
            posrep_beta_max_mm = (NaN,)
            posrep_rss_mm = (NaN,)
            positional_repeatability_has_passed = TestResult.NA
            analysis_results_alpha = None
            analysis_results_beta = None
            posrep_alpha_max_at_angle = []
            posrep_beta_max_at_angle = []
            posrep_alpha_max_mm = NaN
            posrep_beta_max_mm = NaN
            posrep_rss_mm = NaN
            gearbox_correction = None
            min_quality_alpha = NaN
            min_quality_beta = NaN
            arg_max_alpha_error = NaN
            arg_max_beta_error = NaN

        record = PositionalRepeatabilityResults(
            calibration_pars=pos_rep_analysis_pars.POS_REP_CALIBRATION_PARS,
            analysis_results_alpha=analysis_results_alpha,
            analysis_results_beta=analysis_results_beta,
            posrep_alpha_max_at_angle=posrep_alpha_max_at_angle,
            posrep_beta_max_at_angle=posrep_beta_max_at_angle,
            arg_max_alpha_error=arg_max_alpha_error,
            arg_max_beta_error=arg_max_beta_error,
            min_quality_alpha=min_quality_alpha,
            min_quality_beta=min_quality_beta,
            posrep_alpha_max_mm=posrep_alpha_max_mm,
            posrep_beta_max_mm=posrep_beta_max_mm,
            posrep_rss_mm=posrep_rss_mm,
            result=positional_repeatability_has_passed,
            pass_threshold_mm=pos_rep_evaluation_pars.POS_REP_PASS,
            gearbox_correction=gearbox_correction,
            error_message=errmsg,
            algorithm_version=POSITIONAL_REPEATABILITY_ALGORITHM_VERSION,
        )

        save_positional_repeatability_result(dbe, fpu_id, record)
