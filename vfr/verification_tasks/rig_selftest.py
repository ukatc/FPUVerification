from __future__ import absolute_import, division, print_function

import sys
import logging
from os.path import abspath

from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.base import ImageAnalysisError
from ImageAnalysisFuncs.analyze_metrology_calibration import (
    metcalFibreCoordinates,
    metcalTargetCoordinates,
)
from ImageAnalysisFuncs.analyze_metrology_height import methtHeight
from ImageAnalysisFuncs.analyze_positional_repeatability import posrepCoordinates
from ImageAnalysisFuncs.analyze_pupil_alignment import pupilCoordinates
from vfr.conf import (
    MET_CAL_CAMERA_IP_ADDRESS,
    MET_HEIGHT_CAMERA_IP_ADDRESS,
    POS_REP_CAMERA_IP_ADDRESS,
    PUP_ALGN_CAMERA_IP_ADDRESS,
)
from vfr.tests_common import (
    get_sorted_positions,
    store_image,
    timestamp,
    safe_home_turntable,
    turntable_safe_goto,
    home_linear_stage,
    linear_stage_goto,
)


def selftest_pup_algn(rig, pars=None, PUP_ALGN_ANALYSIS_PARS=None, capture_image=None):
    logger = logging.getLogger(__name__)
    logger.info("selftest: pupil alignment")

    try:
        # home turntable
        safe_home_turntable(rig, rig.grid_state)
        home_linear_stage(rig)
        rig.lctrl.switch_all_off()

        with rig.lctrl.use_backlight(5.0):

            # initialize pos_rep camera
            # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
            PUP_ALGN_CAMERA_CONF = {
                DEVICE_CLASS: BASLER_DEVICE_CLASS,
                IP_ADDRESS: PUP_ALGN_CAMERA_IP_ADDRESS,
            }

            pup_aln_cam = rig.hw.GigECamera(PUP_ALGN_CAMERA_CONF)
            pup_aln_cam.SetExposureTime(pars.PUP_ALGN_EXPOSURE_MS)

            fpu_id, lin_position = get_sorted_positions(
                rig.measure_fpuset, pars.PUP_ALGN_LINPOSITIONS
            )[0]

            logger.debug("fpu_id= %s" % fpu_id)
            stage_position = pars.PUP_ALGN_POSITIONS[fpu_id]
            logger.debug("lin_position= %s" % lin_position)
            logger.debug("stage_position= %s" % stage_position)

            # move rotary stage to PUP_ALN_POSN_N
            turntable_safe_goto(rig, rig.grid_state, stage_position)
            linear_stage_goto(rig, lin_position)

            ipath_selftest_pup_algn = capture_image(pup_aln_cam, "pupil-alignment")
            logger.debug(
                "saving pupil alignment image to %r" % abspath(ipath_selftest_pup_algn)
            )

            try:
                result = pupilCoordinates(
                    ipath_selftest_pup_algn, pars=PUP_ALGN_ANALYSIS_PARS
                )
                del result
            except ImageAnalysisError as err:
                if rig.opts.ignore_analysis_failures:
                    logger.warning(
                        "FAILED: self-test pupil alignment image"
                        " analysis (ignored), message = %s" % repr(err)
                    )
                else:
                    logger.error(
                        "image analysis for FPU %s failed with message %r"
                        % (fpu_id, err)
                    )
                    raise

    finally:
        safe_home_turntable(rig, rig.grid_state)
        home_linear_stage(rig)


def selftest_metrology_calibration(
    rig,
    pars=None,
    MET_CAL_TARGET_ANALYSIS_PARS=None,
    MET_CAL_FIBRE_ANALYSIS_PARS=None,
    capture_image=None,
):

    logger = logging.getLogger(__name__)
    logger.info("selftest: metrology calibration")

    try:
        # home turntable
        safe_home_turntable(rig, rig.grid_state)
        home_linear_stage(rig)
        rig.lctrl.switch_all_off()

        MET_CAL_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: MET_CAL_CAMERA_IP_ADDRESS,
        }

        met_cal_cam = rig.hw.GigECamera(MET_CAL_CAMERA_CONF)

        # get sorted positions (here, and only here, we use the linear
        # stage because it is much slower, so using the minimum linear
        # position accelerates the self-test)
        fpu_id, lin_position = get_sorted_positions(
            rig.measure_fpuset, pars.METROLOGY_CAL_LINPOSITIONS
        )[0]

        stage_position = pars.METROLOGY_CAL_POSITIONS[fpu_id]

        # move rotary stage to POS_REP_POSN_0
        turntable_safe_goto(rig, rig.grid_state, stage_position)

        met_cal_cam.SetExposureTime(pars.METROLOGY_CAL_TARGET_EXPOSURE_MS)
        rig.lctrl.switch_all_off()

        # use context manager to switch lamp on
        # and guarantee it is switched off after the
        # measurement (even if exceptions occur)
        with rig.lctrl.use_ambientlight():
            ipath_selftest_met_cal_target = capture_image(met_cal_cam, "met-cal-target")

        logger.debug(
            "saving met cal target image to %r" % abspath(ipath_selftest_met_cal_target)
        )
        met_cal_cam.SetExposureTime(pars.METROLOGY_CAL_FIBRE_EXPOSURE_MS)
        linear_stage_goto(rig, lin_position)
        rig.lctrl.switch_all_off()

        with rig.lctrl.use_backlight(pars.METROLOGY_CAL_BACKLIGHT_VOLTAGE):
            ipath_selftest_met_cal_fibre = capture_image(met_cal_cam, "met-cal-fibre")

        logger.debug(
            "saving met cal fibre image to %r" % abspath(ipath_selftest_met_cal_fibre)
        )
        try:
            target_coordinates = metcalTargetCoordinates(
                ipath_selftest_met_cal_target, pars=MET_CAL_TARGET_ANALYSIS_PARS
            )
            del target_coordinates
        except ImageAnalysisError as err:
            if rig.opts.ignore_analysis_failures:
                logger.warning(
                    "FAILED: self-test metrology calibration image"
                    " analysis (ignored), message = %s" % repr(err)
                )
            else:
                logger.error(
                    "image analysis for FPU %s failed with message %r" % (fpu_id, err)
                )
                raise

        fibre_coordinates = metcalFibreCoordinates(
            ipath_selftest_met_cal_fibre, pars=MET_CAL_FIBRE_ANALYSIS_PARS
        )
        del fibre_coordinates

    finally:
        safe_home_turntable(rig, rig.grid_state)


def selftest_metrology_height(
    rig, MET_HEIGHT_ANALYSIS_PARS=None, pars=None, capture_image=None
):

    logger = logging.getLogger(__name__)
    logger.info("selftest: metrology height")

    try:
        safe_home_turntable(rig, rig.grid_state)
        rig.lctrl.switch_all_off()

        MET_HEIGHT_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: MET_HEIGHT_CAMERA_IP_ADDRESS,
        }

        met_height_cam = rig.hw.GigECamera(MET_HEIGHT_CAMERA_CONF)
        met_height_cam.SetExposureTime(pars.MET_HEIGHT_TARGET_EXPOSURE_MS)

        fpu_id, stage_position = get_sorted_positions(
            rig.measure_fpuset, pars.MET_HEIGHT_POSITIONS
        )[0]

        # move rotary stage to POS_REP_POSN_N
        turntable_safe_goto(rig, rig.grid_state, stage_position)

        with rig.lctrl.use_silhouettelight():
            ipath_selftest_met_height = capture_image(
                met_height_cam, "metrology-height"
            )

        logger.debug(
            "saving met height image to %r" % abspath(ipath_selftest_met_height)
        )
        try:
            metht_small_target_height_mm, metht_large_target_height_mm = methtHeight(
                ipath_selftest_met_height, pars=MET_HEIGHT_ANALYSIS_PARS
            )
            del metht_small_target_height_mm
            del metht_large_target_height_mm

        except ImageAnalysisError as err:
            if rig.opts.ignore_analysis_failures:
                logger.warning(
                    "FAILED: self-test metrology height image"
                    " analysis (ignored), message = %r" % repr(err)
                )
            else:
                logger.error(
                    "image analysis for FPU %s failed with message %r" % (fpu_id, err)
                )
                raise

    finally:
        safe_home_turntable(rig, rig.grid_state)


def selftest_positional_repeatability(
    rig, pars=None, POS_REP_ANALYSIS_PARS=None, capture_image=None
):

    logger = logging.getLogger(__name__)
    logger.info("selftest: positional repeatability")

    try:
        safe_home_turntable(rig, rig.grid_state)
        rig.lctrl.switch_all_off()

        POS_REP_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: POS_REP_CAMERA_IP_ADDRESS,
        }

        pos_rep_cam = rig.hw.GigECamera(POS_REP_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(pars.POS_REP_EXPOSURE_MS)

        fpu_id, stage_position = get_sorted_positions(
            rig.measure_fpuset, pars.POS_REP_POSITIONS
        )[0]

        turntable_safe_goto(rig, rig.grid_state, stage_position)

        with rig.lctrl.use_ambientlight():

            selftest_ipath_pos_rep = capture_image(
                pos_rep_cam, "positional-repeatability"
            )

        logger.debug("saving pos rep image to %r" % abspath(selftest_ipath_pos_rep))
        try:
            coords = posrepCoordinates(
                selftest_ipath_pos_rep, pars=POS_REP_ANALYSIS_PARS
            )
            del coords
        except ImageAnalysisError as err:
            if rig.opts.ignore_analysis_failures:
                logger.warning(
                    "FAILED: self-test positional repeatability image"
                    " analysis (ignored), message = %r" % repr(err)
                )
            else:
                logger.error(
                    "image analysis for FPU %s failed with message %r" % (fpu_id, err)
                )
                raise

    finally:
        safe_home_turntable(rig, rig.grid_state)


def selftest_nonfibre(
    rig,
    MET_HEIGHT_ANALYSIS_PARS=None,
    MET_HEIGHT_MEASUREMENT_PARS=None,
    POS_REP_ANALYSIS_PARS=None,
    POS_REP_MEASUREMENT_PARS=None,
    PUP_ALGN_MEASUREMENT_PARS=None,
):

    logger = logging.getLogger(__name__)
    logger.info("selftest: starting tests without fibre involved")

    tstamp = timestamp()

    def capture_image(cam, subtest):

        ipath = store_image(cam, "self-test/{ts}/{stest}.bmp", ts=tstamp, stest=subtest)
        return ipath

    try:
        selftest_metrology_height(
            rig,
            MET_HEIGHT_ANALYSIS_PARS=MET_HEIGHT_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=MET_HEIGHT_MEASUREMENT_PARS,
        )

    # except Exception as e:
    except SystemError as e:
        logger.critical("metrology height self-test failed:\n\t %s" % repr(e))
        sys.exit(1)

    try:
        selftest_positional_repeatability(
            rig,
            POS_REP_ANALYSIS_PARS=POS_REP_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=POS_REP_MEASUREMENT_PARS,
        )
    except SystemError as e:
        logger.critical("positional repeatability self-test failed %r" % repr(e))
        sys.exit(1)
    logger.info(">>>> selftest: tests without fibre succeeded")


def selftest_fibre(
    rig,
    MET_CAL_MEASUREMENT_PARS=None,
    MET_CAL_FIBRE_ANALYSIS_PARS=None,
    MET_CAL_TARGET_ANALYSIS_PARS=None,
    PUP_ALGN_ANALYSIS_PARS=None,
    PUP_ALGN_MEASUREMENT_PARS=None,
):

    logger = logging.getLogger(__name__)
    logger.info("selftest: starting tests requiring fibre")
    tstamp = timestamp()

    def capture_image(cam, subtest):

        ipath = store_image(cam, "self-test/{ts}/{stest}.bmp", ts=tstamp, stest=subtest)
        return ipath

    try:
        selftest_pup_algn(
            rig,
            PUP_ALGN_ANALYSIS_PARS=PUP_ALGN_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=PUP_ALGN_MEASUREMENT_PARS,
        )

    except SystemError as e:
        logger.critical("pupil alignment self-test failed: %s" % repr(e))
        sys.exit(1)

    try:
        selftest_metrology_calibration(
            rig,
            MET_CAL_TARGET_ANALYSIS_PARS=MET_CAL_TARGET_ANALYSIS_PARS,
            MET_CAL_FIBRE_ANALYSIS_PARS=MET_CAL_FIBRE_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=MET_CAL_MEASUREMENT_PARS,
        )
    except SystemError as e:
        logger.critical("metrology calibration self-test failed %s" % repr(e))
        sys.exit(1)

    logger.info(">>>> selftest: tests requiring fibre succeeded")
