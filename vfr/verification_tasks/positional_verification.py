from __future__ import absolute_import, division, print_function

import random
import warnings
import logging
from os.path import abspath
from os import path
import numpy as np
from vfr.auditlog import get_fpuLogger

from fpu_commands import gen_wf
from Gearbox.gear_correction import (
    GearboxFitError,
    apply_gearbox_correction,
    GEARBOX_CORRECTION_VERSION,
    GEARBOX_CORRECTION_MINIMUM_VERSION,
    cartesian_blob_position
)
from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from DistortionCorrection import get_correction_func
from ImageAnalysisFuncs.base import get_min_quality
from ImageAnalysisFuncs.analyze_positional_repeatability import (
    ImageAnalysisError,
    posrepCoordinates,
    POSITIONAL_REPEATABILITY_ALGORITHM_VERSION,
)
from vfr.evaluation.measures import NO_MEASURES
from vfr.evaluation.eval_positional_verification import evaluate_positional_verification, POS_VER_ALGORITHM_VERSION
from vfr.evaluation.measures import arg_max_dict
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
    fixup_ipath,
    dirac,
    find_datum,
    get_config_from_mapfile,
    get_sorted_positions,
    get_stepcounts,
    store_image,
    timestamp,
    safe_home_turntable,
    turntable_safe_goto,
    check_image_analyzability,
)
from vfr.conf import POS_REP_ANALYSIS_PARS


def generate_calibration_positions(alpha_min, alpha_max, beta_min, number_positions=8):
    """Generate a list of fixed positions to center the FPU within the frame
    """

    positions = []
    
    for k in range(number_positions):
        positions.append(
            (alpha_min + k * (alpha_max - alpha_min) / float(number_positions), beta_min + 10)
        )
    return positions


def generate_tested_positions(
    niterations, alpha_min=NaN, alpha_max=NaN, beta_min=NaN, beta_max=NaN
):
    """Generate a list of random FPU positions for testing
    """
    
    positions = []

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


def read_tested_positions(filename):
    """Read a list of positions from a file
    """
    # Cwd is set for ease of access to moons data, so we have to work out where it should be with 
    abs_filename = path.abspath(path.join(path.dirname(__file__),"../../{}".format(filename)))
    with open(abs_filename,'r') as position_file:
        read_positions = [tuple(map(float, line.split(','))) for line in position_file]
    
    return read_positions


def read_tested_positions_abs(abs_filename):
    """Read a list of positions from the exact file given
    """
    with open(abs_filename,'r') as position_file:
        read_positions = [tuple(map(float, line.split(','))) for line in position_file]
    
    return read_positions


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
                "FPU %s: limits: alpha = %7.2f .. %7.2f" % (sn, alpha_min, alpha_max)
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
                    "FPU %s: positional repeatability data uses old "
                    "version of image analysis, results might be incorrect" % sn
                )

            gearbox_correction_version = pr_result["gearbox_correction_version"]

            if (
                gearbox_correction_version < GEARBOX_CORRECTION_MINIMUM_VERSION
            ):
                fpu_log.error(
                    "FPU %s: positional repeatability result data derived from"
                    " too old version of gearbox correction, skipping measurement."
                    " re-evaluate positional repeatability data to fix this!" % sn
                )

                continue

            if gearbox_correction_version[0] < GEARBOX_CORRECTION_VERSION[0]:
                warnings.warn(
                    "FPU %s: positional repeatability data uses incompatible older"
                    " version of gearbox correction, test skipped - re-compute"
                    " positional compatibility results first" % sn
                )
                continue

            if gearbox_correction_version < GEARBOX_CORRECTION_VERSION:
                warnings.warn(
                    "FPU %s: positional repeatability data uses older"
                    " version of gearbox correction, results might be suboptimal" % sn
                )

            gearbox_correction = pr_result["gearbox_correction"]
            fpu_coeffs = gearbox_correction["coeffs"]
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
                
            def capture_datum_image(timing, number):

                ipath = store_image(
                    pos_rep_cam,
                    "{sn}/{tn}/{ts}/datum-{timing}-{number}.bmp",
                    sn=sn,
                    ts=tstamp,
                    tn="positional-verification",
                    timing=timing,
                    number=number
                )

                return ipath

            tol = abs(pars.POS_VER_SAFETY_TOLERANCE)
            
            # Generate calibation points, make the alpha arm sweep a circle
            calibration_positions = generate_calibration_positions(
                                    alpha_min = alpha_min + tol,
                                    alpha_max = alpha_max - tol,
                                    beta_min = beta_min + tol)
            # Generate positions to be tested, random or read from a file
            if pars.POS_VER_MOTION_FILE:
                test_positions = read_tested_positions(pars.POS_VER_MOTION_FILE)
            else:
                test_positions = generate_tested_positions(
                    pars.POS_VER_ITERATIONS,
                    alpha_min=alpha_min + tol,
                    alpha_max=alpha_max - tol,
                    beta_min=beta_min + tol,
                    beta_max=beta_max - tol,
                )

            tested_positions = calibration_positions + test_positions
        
            datum_image_list=[]

            for i in range(pars.N_DATUM):
                find_datum(gd, grid_state, opts)
                datipath = capture_datum_image("START",i)
                datum_image_list.append(datipath)
                N = opts.N
                # move by delta
                wf = gen_wf(
                    dirac(fpu_id, N) * pars.SMALL_MOVE, dirac(fpu_id, N) * pars.SMALL_MOVE, units="steps"
                )

                gd.configMotion(wf, grid_state, verbosity=0)
                gd.executeMotion(grid_state)
            
            image_dict = {}
            deg2rad = np.deg2rad

            for k, (alpha_deg, beta_deg) in enumerate(tested_positions):
                # get current step count
                alpha_cursteps, beta_cursteps = get_stepcounts(gd, grid_state, fpu_id)

                # get absolute corrected step count from desired absolute angle
                asteps_target, bsteps_target = apply_gearbox_correction(
                    (deg2rad(alpha_deg), deg2rad(beta_deg)), coeffs=fpu_coeffs
                )

                fpu_log.info(
                    "FPU %s: measurement #%i - moving to (%7.2f, %7.2f) degrees = (%i, %i) steps"
                    % (sn, k, alpha_deg, beta_deg, asteps_target, bsteps_target)
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

                ipath = capture_image(k, alpha_deg, beta_deg)
                fpu_log.audit(
                    "saving image for position (%7.3f, %7.3f) to %r"
                    % (alpha_deg, beta_deg, abspath(ipath))
                )
                check_image_analyzability(
                    ipath, posrepCoordinates, pars=POS_REP_ANALYSIS_PARS
                )

                image_dict[(k, alpha_deg, beta_deg)] = ipath

            
            for i in range(pars.N_DATUM):
                find_datum(gd, grid_state, opts)
                datipath = capture_datum_image("END",i)
                datum_image_list.append(datipath)
                N = opts.N
                # move by delta
                wf = gen_wf(
                    dirac(fpu_id, N) * pars.SMALL_MOVE, dirac(fpu_id, N) * pars.SMALL_MOVE, units="steps"
                )

                gd.configMotion(wf, grid_state, verbosity=0)
                gd.executeMotion(grid_state)
            
            # store dict of image paths, together with all data and algorithms
            # which are relevant to assess result later
            record = PositionalVerificationImages(
                images=image_dict,
                gearbox_correction=gearbox_correction,
                gearbox_algorithm_version=GEARBOX_CORRECTION_VERSION,
                gearbox_git_version=gearbox_git_version,
                gearbox_record_count=gearbox_record_count,
                calibration_mapfile=pars.POS_VER_CALIBRATION_MAPFILE,
                datum_images=datum_image_list,
            )

            fpu_log.trace("FPU %r: saving pos_ver image record = %r" % (sn, record))
            save_positional_verification_images(dbe, fpu_id, record)

    logger.info("positional verification captured sucessfully")


def eval_positional_verification(dbe, pos_rep_analysis_pars, pos_ver_evaluation_pars):

    logger = logging.getLogger(__name__)
    for fpu_id in dbe.eval_fpuset:
        sn = dbe.fpu_config[fpu_id]["serialnumber"]
        measurement = get_positional_verification_images(dbe, fpu_id)

        if measurement is None:
            logger.info(
                "FPU %s: no positional verification measurement data found" % sn
            )
            continue

        logger.info("evaluating positional verification for FPU %s" % sn)

        gearbox_algorithm_version = measurement["gearbox_algorithm_version"]
        if gearbox_algorithm_version < GEARBOX_CORRECTION_MINIMUM_VERSION:
            logger.info(
                "FPU %s: positional verification data uses algorithm version %s, "
                "required minimum version is %s. Evaluation skipped."
                % (
                    sn,
                    gearbox_algorithm_version,
                    GEARBOX_CORRECTION_MINIMUM_VERSION,
                )
            )
            continue

        images = measurement["images"]
        gearbox_correction = measurement["gearbox_correction"]
        mapfile = measurement["calibration_mapfile"]
        datum_image_list = measurement["datum_images"]


        ####
        if pos_rep_analysis_pars.TARGET_DETECTION_ALGORITHM == "otsu":
            pars = pos_rep_analysis_pars.TARGET_DETECTION_OTSU_PARS
        else:
            pars = pos_rep_analysis_pars.TARGET_DETECTION_CONTOUR_PARS

        pars.PLATESCALE = pos_rep_analysis_pars.PLATESCALE

        if mapfile:
            pars.CALIBRATION_PARS = get_config_from_mapfile(mapfile)

        correct = get_correction_func(
            calibration_pars=pars.CALIBRATION_PARS,
            platescale=pars.PLATESCALE,
            loglevel=pos_rep_analysis_pars.loglevel,
        )

        ####
        def analysis_func(ipath):
            return posrepCoordinates(fixup_ipath(ipath), pars=pos_rep_analysis_pars, correct=correct)
            
            
#        datum_all_results = []
        datum_results = []
#        middle_point = int(len(datum_image_list)/2)
        for datum_image in datum_image_list:
            datum_blobs = analysis_func(datum_image)
            datum_point = cartesian_blob_position(datum_blobs)
#            datum_all_results.append(datum_point)
            datum_results.append(datum_point)

#      NOTE: Datum results should be filtered in evaluate_positional_verification, not here.
#        # DAtum_image_list is a list of all datums, this includes
#        # a set before and after the verification measurement, with each set having
#        # (perhaps) an unreliable first datum.
#        datum_results = []
#        datum_results.append(sum(datum_all_results[1:middle_point])/ (middle_point-1))
#        datum_results.append(sum(datum_all_results[middle_point+1:])/ (middle_point-1))

        try:
            analysis_results = {}
            count_failures = 0
            count_images = 0

            for k, v in images.items():
                count, alpha_steps, beta_steps, = k
                ipath = v
                try:
                    count_images += 1
                    logger.info("analyzing image {}".format(ipath))
                    analysis_results[k] = analysis_func(ipath)

                except ImageAnalysisError as err:
                    count_failures += 1
                    # ignore image analysis exceptions as long as they are not too frequent
                    if (
                        count_failures
                        > count_images * pos_rep_analysis_pars.MAX_FAILURE_QUOTIENT
                    ):
                        raise
                    else:
                        logger.warning(
                            "image analysis failed for image %s, "
                            "message = %s (continuing)" % (ipath, str(err))
                        )
                        continue

            (posver_error_by_angle, expected_points, measured_points,
             posver_error_measures, mean_error_vector, camera_offset_new, xc, yc) = evaluate_positional_verification(
                 analysis_results, list_of_datum_result=datum_results, pars=pos_ver_evaluation_pars,
                 **gearbox_correction )

            if (95 not in posver_error_measures.percentiles) or np.isnan(
                posver_error_measures.percentiles[95]
            ):
                positional_verification_has_passed = TestResult.NA
            else:
                if (
                    posver_error_measures.percentiles[95]
                    <= pos_ver_evaluation_pars.POS_VER_PASS
                ):
                    positional_verification_has_passed = TestResult.OK
                else:
                    positional_verification_has_passed = TestResult.FAILED

            coords = list(analysis_results.values())
            min_quality = get_min_quality(coords)
            arg_max_error, _ = arg_max_dict(posver_error_by_angle)

            errmsg = ""

        except (ImageAnalysisError, GearboxFitError) as e:
            analysis_results = None
            errmsg = str(e)
            posver_error_by_angle = []
            posver_error_measures = NO_MEASURES
            mean_error_vector = np.array([np.NaN, np.NaN])
            expected_points=[]
            measured_points = []
            positional_verification_has_passed = TestResult.NA
            min_quality = NaN
            arg_max_error = NaN
            logger.exception(
                "image analysis for FPU %s failed with message %s" % (sn, errmsg)
            )

        record = PositionalVerificationResult(
            calibration_pars=pars.CALIBRATION_PARS,
            analysis_results=analysis_results,
            posver_error_measures=posver_error_measures,
            posver_error_by_angle=posver_error_by_angle,
            result=positional_verification_has_passed,
            pass_threshold_mm=pos_ver_evaluation_pars.POS_VER_PASS,
            min_quality=min_quality,
            arg_max_error=arg_max_error,
            expected_points=expected_points,
            measured_points=measured_points,
            mean_error_vector=mean_error_vector,
            error_message=errmsg,
            algorithm_version=GEARBOX_CORRECTION_VERSION,
            evaluation_version=POS_VER_ALGORITHM_VERSION,
            camera_offset=camera_offset_new,
            center_x=xc,
            center_y=yc,
            datum_results=datum_results,
        )
        logger.trace("FPU %r: saving pos_ver result record = %r" % (sn, record))
        save_positional_verification_result(dbe, fpu_id, record)
