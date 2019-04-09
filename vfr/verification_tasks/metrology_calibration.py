from __future__ import absolute_import, division, print_function

from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.analyze_metrology_calibration import (
    METROLOGY_ANALYSIS_ALGORITHM_VERSION,
    ImageAnalysisError,
    fibre_target_distance,
    metcalFibreCoordinates,
    metcalTargetCoordinates,
)
from numpy import NaN
from vfr.conf import MET_CAL_CAMERA_IP_ADDRESS
from vfr.db.metrology_calibration import (
    MetrologyCalibrationImages,
    MetrologyCalibrationResult,
    get_metrology_calibration_images,
    save_metrology_calibration_images,
    save_metrology_calibration_result,
)
from vfr.tests_common import get_sorted_positions, store_image, timestamp


def measure_metrology_calibration(rig, dbe, pars=None):

    tstamp = timestamp()

    # home turntable
    rig.hw.safe_home_turntable(rig.gd, rig.grid_state)
    rig.hw.home_linear_stage()

    rig.lctrl.switch_fibre_backlight("off")
    rig.lctrl.switch_ambientlight("off")
    rig.lctrl.switch_fibre_backlight_voltage(0.0)

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
        # move rotary stage to POS_REP_POSN_N
        rig.hw.turntable_safe_goto(rig.gd, rig.grid_state, stage_position)

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

        met_cal_cam.SetExposureTime(pars.METROLOGY_CAL_FIBRE_EXPOSURE_MS)

        rig.hw.linear_stage_goto(pars.METROLOGY_CAL_LINPOSITIONS[fpu_id])

        with rig.lctrl.use_backlight(pars.METROLOGY_CAL_BACKLIGHT_VOLTAGE):
            fibre_ipath = capture_image(met_cal_cam, "fibre")

        images = {"target": target_ipath, "fibre": fibre_ipath}

        record = MetrologyCalibrationImages(images=images)

        save_metrology_calibration_images(dbe, fpu_id, record)

    rig.hw.home_linear_stage() # bring linear stage to home pos


def eval_metrology_calibration(
    dbe, metcal_target_analysis_pars, metcal_fibre_analysis_pars
):

    for fpu_id in dbe.eval_fpuset:
        measurement = get_metrology_calibration_images(dbe, fpu_id)

        if measurement is None:
            print("FPU %s: no metrology calibration measurement data found" % fpu_id)
            continue

        images = measurement["images"]

        print("images= %r" % images)
        try:
            target_coordinates = metcalTargetCoordinates(
                images["target"], pars=metcal_target_analysis_pars
            )
            fibre_coordinates = metcalFibreCoordinates(
                images["fibre"], pars=metcal_fibre_analysis_pars
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

        record = MetrologyCalibrationResult(
            coords=coords,
            metcal_fibre_large_target_distance_mm=metcal_fibre_large_target_distance_mm,
            metcal_fibre_small_target_distance_mm=metcal_fibre_small_target_distance_mm,
            metcal_target_vector_angle_deg=metcal_target_vector_angle_deg,
            error_message=errmsg,
            algorithm_version=METROLOGY_ANALYSIS_ALGORITHM_VERSION,
        )

        save_metrology_calibration_result(dbe, fpu_id, record)
