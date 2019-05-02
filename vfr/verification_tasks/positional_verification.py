from __future__ import absolute_import, division, print_function

import random
import warnings
import logging
from os.path import abspath
from vfr.auditlog import get_fpuLogger

from fpu_commands import gen_wf
from Gearbox.gear_correction import GearboxFitError, apply_gearbox_correction
from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.base import get_min_quality, arg_max_dict
from ImageAnalysisFuncs.analyze_positional_repeatability import (
    POSITIONAL_REPEATABILITY_ALGORITHM_VERSION,
    ImageAnalysisError,
    evaluate_positional_verification,
    posrepCoordinates,
)
from numpy import NaN
from vfr.conf import POS_REP_CAMERA_IP_ADDRESS
from vfr.db.base import TestResult
from vfr.db.colldect_limits import get_range_limits
from vfr.db.datum_repeatability import get_datum_repeatability_passed_p
from vfr.db.positional_repeatability import (
    get_positional_repeatability_passed_p,
    get_positional_repeatability_result,
)
from vfr.db.positional_verification import (
    PositionalVerificationImages,
    PositionalVerificationResult,
    get_positional_verification_images,
    get_positional_verification_passed_p,
    save_positional_verification_images,
    save_positional_verification_result,
)
from vfr.db.pupil_alignment import get_pupil_alignment_passed_p
from vfr.tests_common import (
    dirac,
    find_datum,
    get_config_from_mapfile,
    get_sorted_positions,
    get_stepcounts,
    store_image,
    timestamp,
    safe_home_turntable,
    turntable_safe_goto,
)


def generate_tested_positions(
    niterations, alpha_min=NaN, alpha_max=NaN, beta_min=NaN, beta_max=NaN
):
    positions = []

    N_FIX_POS = 8
    for k in range(N_FIX_POS):
        positions.append(
            (alpha_min + k * (alpha_max - alpha_min) / float(N_FIX_POS), beta_min + 10)
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


def measure_positional_verification(rig, dbe, pars=None):

    # home turntable
    tstamp = timestamp()
    logger = logging.getLogger(__name__)
    logger.info("capturing positional verification")

    opts = rig.opts
    gd = rig.gd
    grid_state = rig.grid_state

    safe_home_turntable(rig, grid_state)
    rig.lctrl.switch_all_off()

    with rig.lctrl.use_ambientlight():
        # initialize pos_rep camera
        # set pos_rep camera exposure time to POS_VER_EXPOSURE milliseconds
        POS_VER_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: POS_REP_CAMERA_IP_ADDRESS,
        }

        pos_rep_cam = rig.hw.GigECamera(POS_VER_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(pars.POS_VER_EXPOSURE_MS)

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(
            rig.measure_fpuset, pars.POS_REP_POSITIONS
        ):

            fpu_log = get_fpuLogger(fpu_id, rig.fpu_config, __name__)

            sn = rig.fpu_config[fpu_id]["serialnumber"]
            if not get_datum_repeatability_passed_p(dbe, fpu_id):
                fpu_log.info(
                    "FPU %s: skipping positional verification measurement because"
                    " there is no passed datum verification test" % sn
                )
                continue

            if not get_pupil_alignment_passed_p(dbe, fpu_id):
                if opts.skip_fibre:
                    fpu_log.info(
                        "FPU %s: ignoring missing pupil alignment test,\n"
                        " because '--skip-fibre' option is set." % sn
                    )
                else:
                    fpu_log.info(
                        "FPU %s: skipping positional verification measurement,\n"
                        "because there is no passed pupil alignment test \n"
                        "(set option '--skip-fibre' to ignore missing test)" % sn
                    )
                    continue

            if not get_positional_repeatability_passed_p(dbe, fpu_id):
                fpu_log.info(
                    "FPU %s: skipping positional verification measurement because"
                    " there is no passed positional repeatability test" % sn
                )
                continue

            if get_positional_verification_passed_p(dbe, fpu_id) and (
                not opts.repeat_passed_tests
            ):

                fpu_log.info(
                    "FPU %s : positional verification test already passed,"
                    "and flag '--repeat-passed-tests' not set, skipping test" % sn
                )
                continue

            range_limits = get_range_limits(dbe, rig, fpu_id)
            if range_limits is None:
                fpu_log.info("FPU %s : limit test value missing, skipping test" % sn)
                continue

            alpha_min = range_limits.alpha_min
            alpha_max = range_limits.alpha_max
            beta_min = range_limits.beta_min
            beta_max = range_limits.beta_max

            fpu_log.audit(
                "FPU %s: limits: alpha = %7.2f .. %7.2f"
                % (sn, alpha_min, alpha_max)
            )
            fpu_log.audit(
                "FPU %s: limits: beta = %7.2f .. %7.2f" % (sn, beta_min, beta_max)
            )

            if (alpha_min and alpha_max and beta_min and beta_max) is None:
                fpu_log.info(
                    "FPU %s : positional verification test skipped, range limits missing"
                    % sn
                )
                continue

            pr_result = get_positional_repeatability_result(dbe, fpu_id)
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
            gearbox_algorithm_version = pr_result["algorithm_version"]
            gearbox_git_version = pr_result["git_version"]
            gearbox_record_count = pr_result["record-count"]

            # move rotary stage to POS_VER_POSN_N
            turntable_safe_goto(rig, grid_state, stage_position)

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

                fpu_log.info(
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

                gd.configMotion(wf, grid_state, verbosity=0)
                gd.executeMotion(grid_state)

                gd.pingFPUs(grid_state)
                alpha_actualsteps, beta_actualsteps = get_stepcounts(
                    gd, grid_state, fpu_id
                )

                assert (alpha_actualsteps == asteps_target) and (
                    beta_actualsteps == bsteps_target
                ), "could not reach corrected step count"

                fpu_log.debug("FPU %s: saving image # %i..." % (sn, k))

                ipath = capture_image(k, alpha, beta)
                fpu_log.audit("saving image for position (%7.3f, %7.3f) to %r" % (alpha, beta, abspath(ipath)))

                image_dict[(k, alpha, beta)] = ipath

            # store dict of image paths, together with all data and algorithms
            # which are relevant to assess result later
            record = PositionalVerificationImages(
                images=image_dict,
                gearbox_correction=gearbox_correction,
                gearbox_algorithm_version=gearbox_algorithm_version,
                gearbox_git_version=gearbox_git_version,
                gearbox_record_count=gearbox_record_count,
                calibration_mapfile=pars.POS_VER_CALIBRATION_MAPFILE,
            )

            fpu_log.debug("FPU %r: saving result record = %r" % (sn, record))
            save_positional_verification_images(dbe, fpu_id, record)

    logger.info("positional verification captured sucessfully")


def eval_positional_verification(dbe, pos_ver_analysis_pars, pos_ver_evaluation_pars):

    logger = logging.getLogger(__name__)
    for fpu_id in dbe.eval_fpuset:
        measurement = get_positional_verification_images(dbe, fpu_id)

        if measurement is None:
            logger.info("FPU %s: no positional verification measurement data found" % fpu_id)
            continue

        images = measurement["images"]
        mapfile = measurement["calibration_mapfile"]
        if mapfile:
            # passing coefficients is a temporary solution because
            # ultimately we want to pass a function reference to
            # calibrate points, because that's more efficient.
            pos_ver_analysis_pars.POS_REP_CALIBRATION_PARS = get_config_from_mapfile(
                mapfile
            )

            def analysis_func(ipath):
                return posrepCoordinates(ipath, pars=pos_ver_analysis_pars)

        try:
            analysis_results = {}
            analysis_results_short = {}

            for k, v in images.items():
                count, alpha_steps, beta_steps, = k
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

                (posver_error, posver_error_max_mm) = evaluate_positional_verification(
                    analysis_results_short, pars=pos_ver_evaluation_pars
                )

            positional_verification_has_passed = (
                TestResult.OK
                if (posver_error_max_mm <= pos_ver_evaluation_pars.POS_VER_PASS)
                else TestResult.FAILED
            )

            coords = list(analysis_results.values())
            min_quality = get_min_quality(coords)
            arg_max_error, _ = arg_max_dict(posver_error)

            errmsg = ""

        except (ImageAnalysisError, GearboxFitError) as e:
            analysis_results = None
            errmsg = str(e)
            posver_error = ([],)
            posver_error_max_mm = (NaN,)
            positional_verification_has_passed = TestResult.NA
            min_quality = NaN
            arg_max_error = NaN
            logger.exception("image analysis for FPU %s failed with message %s" % (fpu_id, errmsg))

        record = PositionalVerificationResult(
            calibration_pars=pos_ver_analysis_pars.POS_REP_CALIBRATION_PARS,
            analysis_results=analysis_results,
            posver_error=posver_error,
            posver_error_max_mm=posver_error_max_mm,
            result=positional_verification_has_passed,
            pass_threshold_mm=pos_ver_evaluation_pars.POS_VER_PASS,
            min_quality=min_quality,
            arg_max_error=arg_max_error,
            error_message=errmsg,
            algorithm_version=POSITIONAL_REPEATABILITY_ALGORITHM_VERSION,
        )
        logger.debug("FPU %r: saving result record = %r" % (fpu_id, record))
        save_positional_verification_result(dbe, fpu_id, record)
