from __future__ import absolute_import, division, print_function

import warnings
from collections import namedtuple
import logging
from os.path import abspath
from vfr.auditlog import get_fpuLogger

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
from vfr.conf import POS_REP_CAMERA_IP_ADDRESS
from vfr.db.base import TestResult
from vfr.db.colldect_limits import get_range_limits
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
    fixup_ipath,
    find_datum,
    get_config_from_mapfile,
    get_sorted_positions,
    goto_position,
    store_image,
    timestamp,
    safe_home_turntable,
    turntable_safe_goto,
)
from vfr.verification_tasks.measure_datum_repeatability import (
    get_datum_repeatability_passed_p,
)


def check_skip_reason(dbe, fpu_id, sn, repeat_passed_tests=None, skip_fibre=False):
    if not get_datum_repeatability_passed_p(dbe, fpu_id):
        return (
            "FPU %s: skipping positional repeatability measurement because"
            " there is no passed datum repeatability test" % sn
        )

    if not get_pupil_alignment_passed_p(dbe, fpu_id):
        if skip_fibre:
            warnings.warn(
                "skipping check for pupil alignment because '--skip-fibre' flag is set"
            )
        else:
            return (
                "FPU %s: skipping positional repeatability measurement because"
                " there is no passed pupil alignment test"
                " (use '--skip-fibre' flag if you want to omit that test)" % sn
            )

    if get_positional_repeatability_passed_p(dbe, fpu_id) and (not repeat_passed_tests):

        return (
            "FPU %s : positional repeatability test already passed, skipping test" % sn
        )

    return None


def initialize_rig(rig):
    # home turntable
    safe_home_turntable(rig, rig.grid_state)
    # switch lamps off
    rig.lctrl.switch_all_off()


def prepare_cam(rig, exposure_time):
    # initialize pos_rep camera
    # set pos_rep camera exposure time to POSITIONAL_REP_EXPOSURE milliseconds
    POS_REP_CAMERA_CONF = {
        DEVICE_CLASS: BASLER_DEVICE_CLASS,
        IP_ADDRESS: POS_REP_CAMERA_IP_ADDRESS,
    }

    pos_rep_cam = rig.hw.GigECamera(POS_REP_CAMERA_CONF)
    pos_rep_cam.SetExposureTime(exposure_time)

    return pos_rep_cam


MeasurementIndex = namedtuple(
    "MeasurementIndex",
    " i_iteration" " j_direction" " k_increment" " idx_alpha" " idx_beta",
)

FPU_Position = namedtuple("FPU_Position", "alpha beta")


def index_positions(pars):
    for i_iteration in range(pars.POS_REP_ITERATIONS):
        for j_direction in range(4):
            MAX_INCREMENT = pars.POS_REP_NUM_INCREMENTS
            for k_increment in range(MAX_INCREMENT):
                if j_direction == 0:
                    idx_alpha = k_increment
                    idx_beta = 0
                elif j_direction == 1:
                    idx_alpha = MAX_INCREMENT - k_increment - 1
                    idx_beta = 0
                elif j_direction == 2:
                    idx_alpha = 0
                    idx_beta = k_increment
                elif j_direction == 3:
                    idx_alpha = 0
                    idx_beta = MAX_INCREMENT - k_increment - 1

                yield MeasurementIndex(
                    i_iteration, j_direction, k_increment, idx_alpha, idx_beta
                )


def get_target_position(limits, pars, measurement_index):
    alpha_min = limits.alpha_min
    alpha_max = limits.alpha_max
    beta_min = limits.beta_min
    beta_max = limits.beta_max

    step_a = (
        alpha_max - alpha_min - 2 * pars.POS_REP_SAFETY_MARGIN
    ) / pars.POS_REP_NUM_INCREMENTS
    step_b = (
        beta_max - beta_min - 2 * pars.POS_REP_SAFETY_MARGIN
    ) / pars.POS_REP_NUM_INCREMENTS

    alpha0 = alpha_min + pars.POS_REP_SAFETY_MARGIN
    beta0 = beta_min + pars.POS_REP_SAFETY_MARGIN

    abs_alpha = alpha0 + step_a * measurement_index.idx_alpha
    abs_beta = beta0 + step_b * measurement_index.idx_beta

    return FPU_Position(abs_alpha, abs_beta)


def get_counted_angles(rig, fpu_id):
    # to get the angles, we need to pass all connected FPUs
    fpuset = range(rig.opts.N)
    angles = rig.gd.countedAngles(rig.grid_state, fpuset=fpuset)

    alpha_count = angles[fpu_id][0]
    beta_count = angles[fpu_id][1]

    return FPU_Position(alpha_count, beta_count)


def get_step_counts(rig, fpu_id):
    alpha_steps = rig.grid_state.FPU[fpu_id].alpha_steps
    beta_steps = rig.grid_state.FPU[fpu_id].beta_steps

    return FPU_Position(alpha_steps, beta_steps)


def capture_fpu_position(rig, fpu_id, midx, target_pos, capture_image):
    fpu_log = get_fpuLogger(fpu_id, rig.fpu_config, __name__)

    sn = rig.fpu_config[fpu_id]["serialnumber"]
    fpu_log.info(
        "FPU %s measurement [i%2i, j%2i, k%2i]: going to position (%7.2f, %7.2f)"
        % (
            sn,
            midx.i_iteration,
            midx.j_direction,
            midx.k_increment,
            target_pos.alpha,
            target_pos.beta,
        )
    )

    goto_position(
        rig.gd, target_pos.alpha, target_pos.beta, rig.grid_state, fpuset=[fpu_id], loglevel=logging.DEBUG
    )

    # We use the real and uncorrected position to index the images.
    # This has a quantization 'error' compared to the target position,
    # because the stepper motors use discrete steps, of course.
    real_position = get_counted_angles(rig, fpu_id)
    # To compute the gearbox calibration later, we also need the step
    # counts.
    real_steps = get_step_counts(rig, fpu_id)

    ipath = capture_image(midx, real_position)
    fpu_log.audit("saving image for position %r to %r" % (real_position, abspath(ipath)))
    key = (
        real_position.alpha,
        real_position.beta,
        midx.i_iteration,
        midx.j_direction,
        midx.k_increment,
    )
    val = (real_steps.alpha, real_steps.beta, ipath)

    return key, val


def get_images_for_fpu(rig, fpu_id, range_limits, pars, capture_image):

    image_dict_alpha = {}
    image_dict_beta = {}

    current_iteration = -1
    for measurement_index in index_positions(pars):
        # go to datum at start of every new iteration
        if measurement_index.i_iteration != current_iteration:
            find_datum(rig.gd, rig.grid_state, opts=rig.opts)
            current_iteration = measurement_index.i_iteration

        target_pos = get_target_position(range_limits, pars, measurement_index)

        key, val = capture_fpu_position(
            rig, fpu_id, measurement_index, target_pos, capture_image
        )

        # the direction index tells whether the image
        # belongs to the alpha or beta arm series
        image_in_alpha_arm_series = measurement_index.j_direction in [0, 1]

        if image_in_alpha_arm_series:
            image_dict_alpha[key] = val
        else:
            image_dict_beta[key] = val

    record = PositionalRepeatabilityImages(
        images_alpha=image_dict_alpha,
        images_beta=image_dict_beta,
        waveform_pars=pars.POS_REP_WAVEFORM_PARS,
        calibration_mapfile=pars.POS_REP_CALIBRATION_MAPFILE,
    )

    return record


def measure_positional_repeatability(rig, dbe, pars=None):

    tstamp = timestamp()
    logger = logging.getLogger(__name__)
    logger.info("capturing positional repeatability")

    initialize_rig(rig)

    with rig.lctrl.use_ambientlight():
        pos_rep_cam = prepare_cam(rig, pars.POS_REP_EXPOSURE_MS)

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(
            rig.measure_fpuset, pars.POS_REP_POSITIONS
        ):

            fpu_log = get_fpuLogger(fpu_id, rig.fpu_config, __name__)

            sn = rig.fpu_config[fpu_id]["serialnumber"]
            skip_message = check_skip_reason(
                dbe,
                fpu_id,
                sn,
                repeat_passed_tests=rig.opts.repeat_passed_tests,
                skip_fibre=rig.opts.skip_fibre,
            )

            if skip_message:
                fpu_log.info(skip_message)
                continue

            range_limits = get_range_limits(dbe, rig, fpu_id)

            if range_limits is None:
                fpu_log.info("FPU %s : limit test value missing, skipping test" % sn)
                continue

            def capture_image(measurement_index, real_pos):

                ipath = store_image(
                    pos_rep_cam,
                    "{sn}/{tn}/{ts}/i{itr:03d}-j{dir:03d}-k{inc:03d}_({alpha:+08.3f},_{beta:+08.3f}).bmp",
                    sn=sn,
                    tn="positional-repeatability",
                    ts=tstamp,
                    itr=measurement_index.i_iteration,
                    dir=measurement_index.j_direction,
                    inc=measurement_index.k_increment,
                    alpha=real_pos.alpha,
                    beta=real_pos.beta,
                )

                return ipath

            # move rotary stage to POS_REP_POSN_N
            turntable_safe_goto(rig, rig.grid_state, stage_position)

            record = get_images_for_fpu(rig, fpu_id, range_limits, pars, capture_image)
            fpu_log.debug("saving result record = %r" % (record,))

            save_positional_repeatability_images(dbe, fpu_id, record)
    logger.info("positional repeatability captured successfully")


def eval_positional_repeatability(dbe, pos_rep_analysis_pars, pos_rep_evaluation_pars):

    logger = logging.getLogger(__name__)
    for fpu_id in dbe.eval_fpuset:
        measurement = get_positional_repeatability_images(dbe, fpu_id)

        if measurement is None:
            logger.info("FPU %s: no positional repeatability measurement data found" % fpu_id)
            continue

        images_alpha = measurement["images_alpha"]
        images_beta = measurement["images_beta"]

        mapfile = measurement["calibration_mapfile"]
        if mapfile:
            # passing coefficients is a temporary solution because
            # ultimately we want to pass a function reference to
            # calibrate points, because that's more efficient.
            pos_rep_analysis_pars.POS_REP_CALIBRATION_PARS = get_config_from_mapfile(
                mapfile
            )

        def analysis_func(ipath):
            return posrepCoordinates(fixup_ipath(ipath), pars=pos_rep_analysis_pars)

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
            logger.exception("image analysis for FPU %s failed with message %s" % (fpu_id, errmsg))

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

        logger.debug("FPU %r: saving result record = %r" % (fpu_id, record))
        save_positional_repeatability_result(dbe, fpu_id, record)
