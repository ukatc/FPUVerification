from __future__ import print_function, division

from numpy import NaN

from vfr.conf import MET_CAL_CAMERA_IP_ADDRESS

from vfr.db.metrology_calibration import (
    TestResult,
    save_metrology_calibration_images,
    get_metrology_calibration_images,
    save_metrology_calibration_result,
)

from vfr import hw
from vfr import hwsimulation


from GigE.GigECamera import DEVICE_CLASS, BASLER_DEVICE_CLASS, IP_ADDRESS


from vfr.tests_common import (
    flush,
    timestamp,
    dirac,
    goto_position,
    find_datum,
    store_image,
    get_sorted_positions,
)


from ImageAnalysisFuncs.analyze_metrology_calibration import (
    metcalTargetCoordinates,
    metcalFibreCoordinates,
    fibre_target_distance,
    METROLOGY_ANALYSIS_ALGORITHM_VERSION,
)


def measure_metrology_calibration(ctx, pars=None):

    tstamp = timestamp()
    if ctx.opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    # home turntable
    hw.safe_home_turntable(ctx.gd, ctx.grid_state)

    hw.switch_fibre_backlight("off", manual_lamp_control=ctx.opts.manual_lamp_control)
    hw.switch_ambientlight("off", manual_lamp_control=ctx.opts.manual_lamp_control)
    hw.switch_fibre_backlight_voltage(
        0.0, manual_lamp_control=ctx.opts.manual_lamp_control
    )

    MET_CAL_CAMERA_CONF = {
        DEVICE_CLASS: BASLER_DEVICE_CLASS,
        IP_ADDRESS: MET_CAL_CAMERA_IP_ADDRESS,
    }

    met_cal_cam = hw.GigECamera(MET_CAL_CAMERA_CONF)

    # get sorted positions (this is needed because the turntable can only
    # move into one direction)
    for fpu_id, stage_position in get_sorted_positions(
        ctx.measure_fpuset, pars.METROLOGY_CAL_POSITIONS
    ):
        # move rotary stage to POS_REP_POSN_N
        hw.turntable_safe_goto(ctx.gd, ctx.grid_state, stage_position)

        # initialize pos_rep camera
        # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds

        def capture_image(camera, subtest):

            ipath = store_image(
                camera,
                "{sn}/{tn}/{ts}/{st}.bmp",
                sn=fpu_config[fpu_id]["serialnumber"],
                tn="metrology-calibration",
                ts=tstamp,
                st=subtest,
            )

            return ipath

        met_cal_cam.SetExposureTime(pars.METROLOGY_CAL_TARGET_EXPOSURE_MS)
        hw.switch_fibre_backlight(
            "off", manual_lamp_control=ctx.opts.manual_lamp_control
        )
        hw.switch_fibre_backlight_voltage(
            0.0, manual_lamp_control=ctx.opts.manual_lamp_control
        )

        # use context manager to switch lamp on
        # and guarantee it is switched off after the
        # measurement (even if exceptions occur)
        with hw.use_ambientlight(manual_lamp_control=ctx.opts.manual_lamp_control):
            target_ipath = capture_image(met_cal_cam, "target")

        met_cal_cam.SetExposureTime(METROLOGY_CAL_FIBRE_EXPOSURE_MS)

        with use_backlight(
            METROLOGY_CAL_BACKLIGHT_VOLTAGE,
            manual_lamp_control=ctx.opts.manual_lamp_control,
        ):
            fibre_ipath = capture_image(met_cal_cam, "fibre")

        images = {"target": target_ipath, "fibre": fibre_ipath}

        save_metrology_calibration_images(ctx, fpu_id, images)


def eval_metrology_calibration(
    ctx, metcal_target_analysis_pars, metcal_fibre_analysis_pars
):

    for fpu_id in ctx.eval_fpuset:
        images = get_metrology_calibration_images(ctx, fpu_id)

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

            metcal_fibre_large_target_distance, metcal_fibre_small_target_distance, metcal_target_vector_angle = fibre_target_distance(
                target_coordinates[0:2], target_coordinates[3:5], fibre_coordinates[0:2]
            )

            errmsg = None

        except ImageAnalysisError as e:
            errmsg = str(e)
            coords = {}
            metcal_fibre_large_target_distance = NaN
            metcal_fibre_small_target_distance = NaN
            metcal_target_vector_angle = NaN

        save_metrology_calibration_result(
            ctx,
            fpu_id,
            coords=coords,
            metcal_fibre_large_target_distance=metcal_fibre_large_target_distance,
            metcal_fibre_small_target_distance=metcal_fibre_small_target_distance,
            metcal_target_vector_angle=metcal_target_vector_angle,
            errmsg=errmsg,
            analysis_version=METROLOGY_ANALYSIS_ALGORITHM_VERSION,
        )
