from __future__ import absolute_import, division, print_function

from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.analyze_metrology_height import (
    METROLOGY_HEIGHT_ANALYSIS_ALGORITHM_VERSION,
    ImageAnalysisError,
    eval_met_height_inspec,
    methtHeight,
)
from numpy import NaN
from vfr.conf import MET_HEIGHT_CAMERA_IP_ADDRESS
from vfr.db.base import TestResult
from vfr.db.metrology_height import (
    get_metrology_height_images,
    save_metrology_height_images,
    save_metrology_height_result,
)
from vfr.tests_common import (
    get_sorted_positions,
    store_image,
    timestamp,
)


def measure_metrology_height(rig, dbe, pars=None):

    tstamp = timestamp()

    # home turntable
    rig.hw.safe_home_turntable(rig.gd, rig.grid_state)

    rig.lctrl.switch_fibre_backlight("off", manual_lamp_control=rig.opts.manual_lamp_control)
    rig.lctrl.switch_ambientlight("off", manual_lamp_control=rig.opts.manual_lamp_control)
    rig.lctrl.switch_fibre_backlight_voltage(
        0.0, manual_lamp_control=rig.opts.manual_lamp_control
    )

    with rig.lctrl.use_silhouettelight(manual_lamp_control=rig.opts.manual_lamp_control):

        MET_HEIGHT_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: MET_HEIGHT_CAMERA_IP_ADDRESS,
        }

        met_height_cam = rig.hw.GigECamera(MET_HEIGHT_CAMERA_CONF)

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(
            rig.measure_fpuset, pars.MET_HEIGHT_POSITIONS
        ):
            # move rotary stage to POS_REP_POSN_N
            rig.hw.turntable_safe_goto(rig.gd, rig.grid_state, stage_position)

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

            images = capture_image(met_height_cam)

            save_metrology_height_images(dbe, fpu_id, images)


def eval_metrology_height(dbe, met_height_analysis_pars, met_height_evaluation_pars):

    for fpu_id in dbe.eval_fpuset:
        measurement = get_metrology_height_images(dbe, fpu_id)

        if measurement is None:
            print("FPU %s: no metrology height measurement data found" % fpu_id)
            continue

        images = measurement["images"]

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

        save_metrology_height_result(
            dbe,
            fpu_id,
            metht_small_target_height_mm=metht_small_target_height_mm,
            metht_large_target_height_mm=metht_large_target_height_mm,
            test_result=test_result,
            errmsg=errmsg,
            algorithm_version=METROLOGY_HEIGHT_ANALYSIS_ALGORITHM_VERSION,
        )
