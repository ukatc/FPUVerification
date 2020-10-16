from __future__ import absolute_import, division, print_function

import logging
from os.path import abspath
from vfr.auditlog import get_fpuLogger

from functools import partial

from fpu_commands import gen_wf
from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.base import get_min_quality
from ImageAnalysisFuncs.analyze_positional_repeatability import (
    DATUM_REPEATABILITY_ALGORITHM_VERSION,
    ImageAnalysisError,
    posrepCoordinates,
)
from vfr.evaluation.eval_datum_repeatability import (
    evaluate_datum_repeatability,
    NO_RESULT,
)
from numpy import NaN, array
import numpy as np
from vfr.conf import MET_CAL_CAMERA_IP_ADDRESS
from vfr.db.base import TestResult
from vfr.db.datum_repeatability import (
    DatumRepeatabilityImages,
    DatumRepeatabilityResult,
    get_datum_repeatability_images,
    get_datum_repeatability_passed_p,
    save_datum_repeatability_images,
    save_datum_repeatability_result,
)
from vfr.db.colldect_limits import (
    get_anglimit_passed_p,
)
from vfr.tests_common import (
    dirac,
    fixup_ipath,
    get_sorted_positions,
    store_image,
    timestamp,
    safe_home_turntable,
    turntable_safe_goto,
    check_image_analyzability,
)
from DistortionCorrection import get_correction_func
from vfr.conf import DATUM_REP_ANALYSIS_PARS


def check_skip(rig, dbe, fpu_id):
    """checks whether an FPU should be skipped because a previous
    test failed or because it was already tested.
    If so, return the reason as a string."""

    if not get_anglimit_passed_p(dbe, fpu_id, 'alpha_min'):
        return (
            "FPU %s: skipping datum repeatability measurement because"
            " there is no passed alpha_min limit test" % sn
        )
    if not get_anglimit_passed_p(dbe, fpu_id, 'alpha_max'):
        return (
            "FPU %s: skipping datum repeatability measurement because"
            " there is no passed alpha_max limit test" % sn
        )
    if not get_anglimit_passed_p(dbe, fpu_id, 'beta_min'):
        return (
            "FPU %s: skipping datum repeatability measurement because"
            " there is no passed beta_min limit test" % sn
        )
    if not get_anglimit_passed_p(dbe, fpu_id, 'beta_max'):
        return (
            "FPU %s: skipping datum repeatability measurement because"
            " there is no passed beta_min limit test" % sn
        )
    if not get_anglimit_passed_p(dbe, fpu_id, 'beta_collision'):
        return (
            "FPU %s: skipping datum repeatability measurement because"
            " there is no passed beta collision test" % sn
        )

    if get_datum_repeatability_passed_p(dbe, fpu_id) and (
        not rig.opts.repeat_passed_tests
    ):

        sn = rig.fpu_config[fpu_id]["serialnumber"]
        return "FPU %{} : datum repeatability test already passed, skipping test".format(
            sn
        )

    # no reason found, return a falsey value
    return None


def config_camera(rig, exposure_time):
    """configure the camera, returning a camera object."""

    # initialize camera
    # set camera exposure time to DATUM_REP_EXPOSURE milliseconds
    MET_CAL_CAMERA_CONF = {
        DEVICE_CLASS: BASLER_DEVICE_CLASS,
        IP_ADDRESS: MET_CAL_CAMERA_IP_ADDRESS,
    }

    met_cal_cam = rig.hw.GigECamera(MET_CAL_CAMERA_CONF)
    met_cal_cam.SetExposureTime(exposure_time)

    return met_cal_cam


def get_counter_residuals(rig, fpu_id):
    """get residual step countes for a specific FPU
    from the grid_state data structure.

    These residual values indicate when an FPU was missing
    steps during a movement, because normally
    the step numbers at dataum cancel out to zero.
    """

    # getCounterDeviation is now obsolete. Can just query and use the grid state.
    #rig.gd.getCounterDeviation(rig.grid_state, fpuset=[fpu_id])
    rig.gd.pingFPUs(rig.grid_state, fpuset=[fpu_id])
    fpu = rig.grid_state.FPU[fpu_id]
    return (fpu.alpha_deviation, fpu.beta_deviation)


def move_then_datum(rig, fpu_id):
    """make a measurement where an FPU is first moved,
    then datumed, so that impact of movements on
    the FPUs mechanical precision is measured.
    """
    fpu_log = get_fpuLogger(fpu_id, rig.fpu_config, __name__)
    fpu_log.audit("moving FPU %i to (30,30) and back" % fpu_id)

    wf = gen_wf(30 * dirac(fpu_id, rig.opts.N), 30)
    gd = rig.gd
    grid_state = rig.grid_state

    gd.configMotion(wf, grid_state, verbosity=0)
    gd.executeMotion(grid_state, fpuset=[fpu_id])
    gd.reverseMotion(grid_state, fpuset=[fpu_id], verbosity=0)
    gd.executeMotion(grid_state, fpuset=[fpu_id])
    # Find the datum twice. The second time is more accurate than the first.
    gd.findDatum(grid_state, fpuset=[fpu_id])
    gd.findDatum(grid_state, fpuset=[fpu_id])


def grab_datumed_images(rig, fpu_id, capture_func, iterations):
    """perform a number of datum operations, store
    an image after each, and return the path names
    of the images, together with the residual count."""
    fpu_log = get_fpuLogger(fpu_id, rig.fpu_config, __name__)

    datumed_images = []
    datumed_residuals = []
    for count in range(iterations):

        fpu_log = get_fpuLogger(fpu_id, rig.fpu_config, __name__)
        fpu_log.info("capturing datumed-%02i" % count)

        # Find the datum twice. The second time is more accurate than the first.
        rig.gd.findDatum(rig.grid_state, fpuset=[fpu_id])
        rig.gd.findDatum(rig.grid_state, fpuset=[fpu_id])

        ipath = capture_func("datumed", count)
        fpu_log.audit("saving image %i to %r" % (count, abspath(ipath)))
        check_image_analyzability(
            ipath, posrepCoordinates, pars=DATUM_REP_ANALYSIS_PARS
        )
        datumed_images.append(ipath)

        alpha_dev, beta_dev = get_counter_residuals(rig, fpu_id)
        datumed_residuals.append((alpha_dev, beta_dev))

    return datumed_images, datumed_residuals


def grab_moved_images(rig, fpu_id, capture_func, iterations):
    """perform datum operations after moving, grab and
    collect images, and return resulting images and residual counts.
    """

    fpu_log = get_fpuLogger(fpu_id, rig.fpu_config, __name__)

    # Find the datum twice. The second time is more accurate than the first.
    rig.gd.findDatum(rig.grid_state)
    rig.gd.findDatum(rig.grid_state)
    moved_images = []
    moved_residuals = []
    for count in range(iterations):
        move_then_datum(rig, fpu_id)

        fpu_log.info("capturing moved+datumed-%02i" % count)
        ipath = capture_func("moved+datumed", count)
        fpu_log.audit("saving image %i to %r" % (count, abspath(ipath)))
        check_image_analyzability(
            ipath, posrepCoordinates, pars=DATUM_REP_ANALYSIS_PARS
        )
        moved_images.append(ipath)

        alpha_dev, beta_dev = get_counter_residuals(rig, fpu_id)
        moved_residuals.append((alpha_dev, beta_dev))

    return moved_images, moved_residuals


def record_images_from_fpu(rig, fpu_id, capture_image, num_iterations):
    """make a mesaurement series for a specific FPU."""

    sn = rig.fpu_config[fpu_id]["serialnumber"]
    capture_for_sn = partial(capture_image, sn)

    # capture images with datum-only hardware command
    datumed_images, datumed_residuals = grab_datumed_images(
        rig, fpu_id, capture_for_sn, num_iterations
    )

    # capture images whith FPU moveing, then datum
    moved_images, moved_residuals = grab_moved_images(
        rig, fpu_id, capture_for_sn, num_iterations
    )

    # wrap up the gathered data in a DB record
    image_record = DatumRepeatabilityImages(
        images={"datumed_images": datumed_images, "moved_images": moved_images},
        residual_counts={
            "datumed_residuals": datumed_residuals,
            "moved_residuals": moved_residuals,
        },
    )

    return image_record


def measure_datum_repeatability(rig, dbe, pars=None):
    # go to defined start configuration
    safe_home_turntable(rig, rig.grid_state)
    rig.lctrl.switch_all_off()
    logger = logging.getLogger(__name__)
    logger.info("capturing datum repeatability")

    with rig.lctrl.use_ambientlight():

        tstamp = timestamp()
        camera = config_camera(rig, pars.DATUM_REP_EXPOSURE_MS)

        # define closure which stores images with unique path names
        # (using time stamp and camera object configured above)
        def capture_image(sn, subtest, cnt):
            ipath = store_image(
                camera,
                "{sn}/{tn}/{ts}/{tp}-{ct:03d}.bmp",
                sn=sn,
                tn="datum-repeatability",
                ts=tstamp,
                tp=subtest,
                ct=cnt,
            )

            return ipath

        # turn table along sorted positions
        for fpu_id, stage_position in get_sorted_positions(
            rig.measure_fpuset, pars.DATUM_REP_POSITIONS
        ):

            fpu_log = get_fpuLogger(fpu_id, rig.fpu_config, __name__)
            skip_reason = check_skip(rig, dbe, fpu_id)
            if skip_reason:
                fpu_log.info(skip_reason)
                continue

            # move rotary stage to measurement position
            turntable_safe_goto(rig, rig.grid_state, stage_position)
            # measure images
            image_record = record_images_from_fpu(
                rig, fpu_id, capture_image, pars.DATUM_REP_ITERATIONS
            )
            # store to database
            save_datum_repeatability_images(dbe, fpu_id, image_record)

    logger.info("datum repeatability successfully captured")


def eval_datum_repeatability(dbe, dat_rep_analysis_pars):

    logger = logging.getLogger(__name__)

    for fpu_id in dbe.eval_fpuset:
        sn = dbe.fpu_config[fpu_id]["serialnumber"]
        measurement = get_datum_repeatability_images(dbe, fpu_id)
        if measurement is None:
            logger.info(
                "FPU %s: no datum repeatability measurement data found" % sn
            )
            continue

        logger.info("evaluating datum repeatability for FPU %s" % sn)

        images = measurement["images"]

        residual_counts = measurement["residual_counts"]

        if dat_rep_analysis_pars.TARGET_DETECTION_ALGORITHM == "otsu":
            pars = dat_rep_analysis_pars.TARGET_DETECTION_OTSU_PARS
        else:
            pars = dat_rep_analysis_pars.TARGET_DETECTION_CONTOUR_PARS

        pars.PLATESCALE = dat_rep_analysis_pars.PLATESCALE

        correct = get_correction_func(
            calibration_pars=pars.CALIBRATION_PARS,
            platescale=pars.PLATESCALE,
            loglevel=dat_rep_analysis_pars.loglevel,
        )

        def analysis_func(ipath):
            return posrepCoordinates(
                fixup_ipath(ipath), pars=dat_rep_analysis_pars, correct=correct
            )

        try:
            count_images = len(images["datumed_images"]) + len(images["moved_images"])
            count_failures = 0
            datumed_coords = []
            for ipath in images["datumed_images"]:
                try:
                    datumed_coords.append(analysis_func(ipath))
                except ImageAnalysisError as err:
                    count_failures += 1
                    if (
                        count_failures
                        > count_images * dat_rep_analysis_pars.MAX_FAILURE_QUOTIENT
                    ):
                        raise
                    else:
                        logger.warning(
                            "image analysis failed for image %s, "
                            "message = %s (continuing)" % (ipath, str(err))
                        )
                        continue

            moved_coords = []
            for ipath in images["moved_images"]:
                try:
                    moved_coords.append(analysis_func(ipath))
                except ImageAnalysisError as err:
                    count_failures += 1
                    if (
                        count_failures
                        > count_images * dat_rep_analysis_pars.MAX_FAILURE_QUOTIENT
                    ):
                        raise
                    else:
                        logger.warning(
                            "image analysis failed for image %s, "
                            "message = %s (continuing)" % (ipath, str(err))
                        )
                        continue

            error_measures = evaluate_datum_repeatability(datumed_coords, moved_coords)

            datum_repeatability_has_passed = (
                TestResult.OK
                if (
                    error_measures.combined.percentiles[
                        dat_rep_analysis_pars.DATUM_REP_TESTED_PERCENTILE
                    ]
                    <= dat_rep_analysis_pars.DATUM_REP_PASS
                )
                else TestResult.FAILED
            )

            coords = {"datumed_coords": datumed_coords, "moved_coords": moved_coords}
            errmsg = ""
            max_residual_datumed = np.max(array(residual_counts["datumed_residuals"]))
            max_residual_moved = np.max(array(residual_counts["moved_residuals"]))

            min_quality_datumed = get_min_quality(datumed_coords)

            min_quality_moved = get_min_quality(moved_coords)

        except ImageAnalysisError as e:
            errmsg = str(e)
            coords = {}

            datum_repeatability_has_passed = TestResult.NA
            max_residual_datumed = NaN
            max_residual_moved = NaN
            min_quality_datumed = NaN
            min_quality_moved = NaN
            error_measures = NO_RESULT

            logger.exception(
                "image analysis for FPU %s failed with message %s" % (sn, errmsg)
            )

        record = DatumRepeatabilityResult(
            algorithm_version=DATUM_REPEATABILITY_ALGORITHM_VERSION,
            coords=coords,
            datum_repeatability_max_residual_datumed=max_residual_datumed,
            datum_repeatability_max_residual_moved=max_residual_moved,
            datum_repeatability_datum_only=error_measures.datum_only,
            datum_repeatability_moved=error_measures.moved,
            datum_repeatability_combined=error_measures.combined,
            error_message=errmsg,
            min_quality_datumed=min_quality_datumed,
            min_quality_moved=min_quality_moved,
            pass_threshold_mm=dat_rep_analysis_pars.DATUM_REP_PASS,
            result=datum_repeatability_has_passed,
        )

        logger.trace("FPU %r: saving datum rep result record = %r" % (sn, record))
        save_datum_repeatability_result(dbe, fpu_id, record)
