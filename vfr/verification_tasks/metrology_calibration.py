from __future__ import absolute_import, division, print_function

import logging
from os.path import abspath
from vfr.auditlog import get_fpuLogger
from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.analyze_metrology_calibration import (
    METROLOGY_ANALYSIS_ALGORITHM_VERSION,
    ImageAnalysisError,
    metcalFibreCoordinates,
    metcalTargetCoordinates,
)
from vfr.evaluation.eval_metrology_calibration import fibre_target_distance
from numpy import NaN
from vfr.conf import MET_CAL_CAMERA_IP_ADDRESS
from vfr.db.metrology_calibration import (
    MetrologyCalibrationImages,
    MetrologyCalibrationResult,
    get_metrology_calibration_images,
    save_metrology_calibration_images,
    save_metrology_calibration_result,
)
from vfr.tests_common import (
    fixup_ipath,
    get_sorted_positions,
    store_image,
    timestamp,
    safe_home_turntable,
    turntable_safe_goto,
    home_linear_stage,
    linear_stage_goto,
    check_image_analyzability,
)
from vfr.conf import MET_CAL_TARGET_ANALYSIS_PARS, MET_CAL_FIBRE_ANALYSIS_PARS


def measure_metrology_calibration(rig, dbe, pars=None):

    tstamp = timestamp()

    logger = logging.getLogger(__name__)
    logger.info("capturing metrology calibration")
    # home turntable
    safe_home_turntable(rig, rig.grid_state)
    home_linear_stage(rig)
    rig.lctrl.switch_all_off()

    MET_CAL_CAMERA_CONF = {
        DEVICE_CLASS: BASLER_DEVICE_CLASS,
        IP_ADDRESS: MET_CAL_CAMERA_IP_ADDRESS,
    }

    met_cal_cam = rig.hw.GigECamera(MET_CAL_CAMERA_CONF)

    # get sorted positions (this is needed because the turntable can only
    # move into one direction)
    for fpu_id, stage_position in get_sorted_positions(
        rig.measure_fpuset, pars.METROLOGY_CAL_POSITIONS
    ):
        fpu_log = get_fpuLogger(fpu_id, rig.fpu_config, __name__)
        fpu_log.info("capturing metrology calibration")

        # move rotary stage to POS_REP_POSN_N
        turntable_safe_goto(rig, rig.grid_state, stage_position)

        # initialize pos_rep camera
        # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds

        def capture_image(camera, subtest):

            ipath = store_image(
                camera,
                "{sn}/{tn}/{ts}/{st}.bmp",
                sn=rig.fpu_config[fpu_id]["serialnumber"],
                tn="metrology-calibration",
                ts=tstamp,
                st=subtest,
            )

            return ipath

        met_cal_cam.SetExposureTime(pars.METROLOGY_CAL_TARGET_EXPOSURE_MS)
        rig.lctrl.switch_fibre_backlight("off")
        rig.lctrl.switch_fibre_backlight_voltage(0.0)

        # use context manager to switch lamp on
        # and guarantee it is switched off after the
        # measurement (even if exceptions occur)
        with rig.lctrl.use_ambientlight():
            target_ipath = capture_image(met_cal_cam, "target")

        fpu_log.audit("saving target image to %r" % abspath(target_ipath))
        check_image_analyzability(
            target_ipath, metcalTargetCoordinates, pars=MET_CAL_TARGET_ANALYSIS_PARS
        )
        met_cal_cam.SetExposureTime(pars.METROLOGY_CAL_FIBRE_EXPOSURE_MS)

        linear_stage_goto(rig, pars.METROLOGY_CAL_LINPOSITIONS[fpu_id])

        with rig.lctrl.use_backlight(pars.METROLOGY_CAL_BACKLIGHT_VOLTAGE):
            fibre_ipath = capture_image(met_cal_cam, "fibre")

        fpu_log.audit("saving fibre image to %r" % abspath(fibre_ipath))
        check_image_analyzability(
            fibre_ipath, metcalFibreCoordinates, pars=MET_CAL_FIBRE_ANALYSIS_PARS
        )
        images = {"target": target_ipath, "fibre": fibre_ipath}

        record = MetrologyCalibrationImages(images=images)
        fpu_log.debug("saving result to %r" % record)
        save_metrology_calibration_images(dbe, fpu_id, record)

    home_linear_stage(rig)  # bring linear stage to home pos
    logger.info("metrology calibration captured successfully")


def eval_metrology_calibration(
    dbe, metcal_target_analysis_pars, metcal_fibre_analysis_pars
):

    logger = logging.getLogger(__name__)
    for fpu_id in dbe.eval_fpuset:
        measurement = get_metrology_calibration_images(dbe, fpu_id)

        if measurement is None:
            logger.info(
                "FPU %s: no metrology calibration measurement data found" % fpu_id
            )
            continue

        logger.info("evaluating metrology calibration for FPU %s" % fpu_id)

        images = measurement["images"]

        logger.debug("images= %r" % images)
        try:
            target_coordinates = metcalTargetCoordinates(
                fixup_ipath(images["target"]), pars=metcal_target_analysis_pars
            )
            fibre_coordinates = metcalFibreCoordinates(
                fixup_ipath(images["fibre"]), pars=metcal_fibre_analysis_pars
            )

            coords = {
                "target_small_xy": target_coordinates[0:2],
                "target_small_q": target_coordinates[2],
                "target_big_xy": target_coordinates[3:5],
                "target_big_q": target_coordinates[5],
                "fibre_xy": fibre_coordinates[0:2],
                "fibre_q": fibre_coordinates[2],
            }

            metcal_fibre_large_target_distance_mm, metcal_fibre_small_target_distance_mm, metcal_target_vector_angle_deg = fibre_target_distance(
                target_coordinates[0:2], target_coordinates[3:5], fibre_coordinates[0:2]
            )

            errmsg = None

        except ImageAnalysisError as e:
            errmsg = str(e)
            coords = {}
            metcal_fibre_large_target_distance_mm = NaN
            metcal_fibre_small_target_distance_mm = NaN
            metcal_target_vector_angle_deg = NaN
            logger.exception(
                "image analysis for FPU %s failed with message %s" % (fpu_id, errmsg)
            )

        record = MetrologyCalibrationResult(
            coords=coords,
            metcal_fibre_large_target_distance_mm=metcal_fibre_large_target_distance_mm,
            metcal_fibre_small_target_distance_mm=metcal_fibre_small_target_distance_mm,
            metcal_target_vector_angle_deg=metcal_target_vector_angle_deg,
            error_message=errmsg,
            algorithm_version=METROLOGY_ANALYSIS_ALGORITHM_VERSION,
        )

        logger.debug("FPU %r: saving result record = %r" % (fpu_id, record))
        save_metrology_calibration_result(dbe, fpu_id, record)
