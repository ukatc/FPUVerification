from __future__ import absolute_import, division, print_function

from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.analyze_metrology_height import (
    METROLOGY_HEIGHT_ANALYSIS_ALGORITHM_VERSION,
    ImageAnalysisError,
    eval_met_height_inspec,
    methtHeight,
)
from numpy import NaN
import logging
from os.path import abspath
from vfr.auditlog import get_fpuLogger
from vfr.conf import MET_HEIGHT_CAMERA_IP_ADDRESS
from vfr.db.base import TestResult
from vfr.db.metrology_height import (
    MetrologyHeightImages,
    MetrologyHeightResult,
    get_metrology_height_images,
    save_metrology_height_images,
    save_metrology_height_result,
)
from vfr.tests_common import (
    fixup_ipath,
    get_sorted_positions,
    store_image,
    timestamp,
    safe_home_turntable,
    turntable_safe_goto,
    check_image_analyzability,
)
from vfr.conf import MET_HEIGHT_ANALYSIS_PARS

def measure_metrology_height(rig, dbe, pars=None):

    tstamp = timestamp()

    logger = logging.getLogger(__name__)
    logger.info("capturing metrology height")
    # home turntable
    safe_home_turntable(rig, rig.grid_state)
    rig.lctrl.switch_all_off()


    MET_HEIGHT_CAMERA_CONF = {
        DEVICE_CLASS: BASLER_DEVICE_CLASS,
        IP_ADDRESS: MET_HEIGHT_CAMERA_IP_ADDRESS,
    }

    met_height_cam = rig.hw.GigECamera(MET_HEIGHT_CAMERA_CONF)
    met_height_cam.SetExposureTime(pars.MET_HEIGHT_TARGET_EXPOSURE_MS)

    # get sorted positions (this is needed because the turntable can only
    # move into one direction)
    for fpu_id, stage_position in get_sorted_positions(
        rig.measure_fpuset, pars.MET_HEIGHT_POSITIONS
    ):
        fpu_log = get_fpuLogger(fpu_id, rig.fpu_config, __name__)
        fpu_log.info("capturing metrology height image")
        # move rotary stage to POS_REP_POSN_N
        turntable_safe_goto(rig, rig.grid_state, stage_position)

        # initialize pos_rep camera
        # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds

        def capture_image(camera):

            ipath = store_image(
                camera,
                "{sn}/{tn}/{ts}.bmp",
                sn=rig.fpu_config[fpu_id]["serialnumber"],
                tn="metrology-height",
                ts=tstamp,
            )

            return ipath

        with rig.lctrl.use_silhouettelight():
            ipath = capture_image(met_height_cam)
        fpu_log.audit("saving height image to %r" % abspath(ipath))
        check_image_analyzability(ipath, methtHeight, pars=MET_HEIGHT_ANALYSIS_PARS)

        record = MetrologyHeightImages(images=ipath)
        fpu_log.debug("saving result record = %r" % record)
        save_metrology_height_images(dbe, fpu_id, record)
    logger.info("metrology height captured successfully")


def eval_metrology_height(dbe, met_height_analysis_pars, met_height_evaluation_pars):

    logger = logging.getLogger(__name__)
    for fpu_id in dbe.eval_fpuset:
        measurement = get_metrology_height_images(dbe, fpu_id)

        if measurement is None:
            logger.info("FPU %s: no metrology height measurement data found" % fpu_id)
            continue

        logger.info("evaluating metrology height for FPU %s" % fpu_id)

        images = fixup_ipath(measurement["images"])

        try:

            metht_small_target_height_mm, metht_large_target_height_mm = methtHeight(
                images, pars=met_height_analysis_pars
            )

            result_in_spec = eval_met_height_inspec(
                metht_small_target_height_mm,
                metht_large_target_height_mm,
                pars=met_height_evaluation_pars,
            )

            test_result = TestResult.OK if result_in_spec else TestResult.FAILED

            errmsg = None

        except ImageAnalysisError as e:
            errmsg = str(e)
            metht_small_target_height_mm = NaN
            metht_large_target_height_mm = NaN
            test_result = TestResult.NA
            logger.exception("image analysis for FPU %s failed with message %s" % (fpu_id, errmsg))

        record = MetrologyHeightResult(
            small_target_height_mm=metht_small_target_height_mm,
            large_target_height_mm=metht_large_target_height_mm,
            test_result=test_result,
            error_message=errmsg,
            algorithm_version=METROLOGY_HEIGHT_ANALYSIS_ALGORITHM_VERSION,
        )
        logger.debug("FPU %r: saving result record = %r" % (fpu_id, record))
        save_metrology_height_result(dbe, fpu_id, record)
