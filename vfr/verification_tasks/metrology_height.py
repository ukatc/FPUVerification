from __future__ import print_function, division

from numpy import NaN

from vfr.conf import MET_HEIGHT_CAMERA_IP_ADDRESS

from vfr.db.metrology_height import (
    TestResult,
    save_metrology_height_images,
    get_metrology_height_images,
    save_metrology_height_result,
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


from ImageAnalysisFuncs.analyze_metrology_height import (
    methtHeight,
    eval_met_height_inspec,
    METROLOGY_HEIGHT_ANALYSIS_ALGORITHM_VERSION,
)


def measure_metrology_height(ctx, parse=None):

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

    with hw.use_silhouettelight(manual_lamp_control=ctx.opts.manual_lamp_control):

        MET_HEIGHT_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: MET_HEIGHT_CAMERA_IP_ADDRESS,
        }

        met_height_cam = hw.GigECamera(MET_HEIGHT_CAMERA_CONF)

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(
            ctx.measure_fpuset, pars.METROLOGY_HEIGHT_POSITIONS
        ):
            # move rotary stage to POS_REP_POSN_N
            hw.turntable_safe_goto(ctx.gd, ctx.grid_state, stage_position)

            # initialize pos_rep camera
            # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds

            def capture_image(camera):

                ipath = store_image(
                    camera,
                    "{sn}/{tn}/{ts}.bmp",
                    sn=ctx.fpu_config[fpu_id]["serialnumber"],
                    tn="metrology-height",
                    ts=tstamp,
                )

                return ipath

            images = capture_image(met_height_cam)

            save_metrology_height_images(ctx, fpu_id, images)


def eval_metrology_height(ctx, met_height_analysis_pars, met_height_evaluation_pars):

    for fpu_id in ctx.eval_fpuset:
        image = get_metrology_height_images(ctx, fpu_id)

        try:

            metht_small_target_height, metht_large_target_height = methtHeight(
                image, pars=met_height_analysis_pars
            )

            result_in_spec = eval_met_height_inspec(
                metht_small_target_height,
                metht_large_target_height,
                pars=met_height_evaluation_pars,
            )

            result = TestResult.OK if result_in_spec else TestResult.FAILED

            errmsg = None

        except ImageAnalysisError as e:
            errmsg = str(e)
            metht_small_target_height = NaN
            metht_large_target_height = NaN
            result = TestResult.NA

        save_metrology_height_result(
            ctx,
            fpu_id,
            metht_small_target_height=metht_small_target_height,
            metht_large_target_height=metht_large_target_height,
            test_result=testResult,
            errmsg=errmsg,
            analysis_version=METROLOGY_HEIGHT_ANALYSIS_ALGORITHM_VERSION,
        )
