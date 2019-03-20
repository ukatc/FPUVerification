from __future__ import print_function, division

import sys

from vfr.conf import (
    PUP_ALGN_CAMERA_IP_ADDRESS,
    POS_REP_CAMERA_IP_ADDRESS,
    MET_CAL_CAMERA_IP_ADDRESS,
    MET_HEIGHT_CAMERA_IP_ADDRESS,
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

from ImageAnalysisFuncs.analyze_pupil_alignment import (
    pupalnCoordinates,
    evaluate_pupil_alignment,
)

from ImageAnalysisFuncs.analyze_metrology_calibration import (
    metcalTargetCoordinates,
    metcalFibreCoordinates,
)

from ImageAnalysisFuncs.analyze_metrology_height import methtHeight

from ImageAnalysisFuncs.analyze_positional_repeatability import posrepCoordinates


def selftest_pup_algn(ctx, pars=None, PUP_ALGN_ANALYSIS_PARS=None, capture_image=None):
    print ("selftest: pupil alignment")
    if ctx.opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    try:
        # home turntable
        hw.safe_home_turntable(ctx.gd, ctx.grid_state)
        hw.home_linear_stage()

        hw.switch_ambientlight("off", manual_lamp_control=ctx.opts.manual_lamp_control)
        hw.switch_silhouettelight(
            "off", manual_lamp_control=ctx.opts.manual_lamp_control
        )

        with hw.use_backlight(5.0, manual_lamp_control=ctx.opts.manual_lamp_control):

            # initialize pos_rep camera
            # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
            PUP_ALGN_CAMERA_CONF = {
                DEVICE_CLASS: BASLER_DEVICE_CLASS,
                IP_ADDRESS: PUP_ALGN_CAMERA_IP_ADDRESS,
            }

            pup_aln_cam = hw.GigECamera(PUP_ALGN_CAMERA_CONF)
            pup_aln_cam.SetExposureTime(pars.PUP_ALGN_EXPOSURE_MS)

            fpu_id, stage_position = get_sorted_positions(
                ctx.measure_fpuset, pars.PUP_ALGN_POSITIONS
            )[0]

            # move rotary stage to PUP_ALN_POSN_N
            hw.turntable_safe_goto(ctx.gd, ctx.grid_state, stage_position)
            hw.linear_stage_goto(pars.PUP_ALGN_LINPOSITIONS[fpu_id])

            ipath_selftest_pup_algn = capture_image(pup_aln_cam, "pupil-alignment")

            result = pupalnCoordinates(
                ipath_selftest_pup_algn, pars=PUP_ALGN_ANALYSIS_PARS
            )
    finally:
        hw.safe_home_turntable(ctx.gd, ctx.grid_state)
        hw.home_linear_stage()


def selftest_metrology_calibration(
    ctx,
    pars=None,
    MET_CAL_TARGET_ANALYSIS_PARS=None,
    MET_CAL_FIBRE_ANALYSIS_PARS=None,
    capture_image=None,
):

    print ("selftest: metrology calibration")
    if ctx.opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    try:
        # home turntable
        hw.safe_home_turntable(ctx.gd, ctx.grid_state)

        hw.switch_fibre_backlight(
            "off", manual_lamp_control=ctx.opts.manual_lamp_control
        )
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
        fpu_id, stage_position = get_sorted_positions(
            ctx.measure_fpuset, pars.METROLOGY_CAL_POSITIONS
        )[0]

        # move rotary stage to POS_REP_POSN_0
        hw.turntable_safe_goto(ctx.gd, ctx.grid_state, stage_position)

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
            ipath_selftest_met_cal_target = capture_image(met_cal_cam, "met-cal-target")

        met_cal_cam.SetExposureTime(pars.METROLOGY_CAL_FIBRE_EXPOSURE_MS)
        hw.switch_ambientlight("off", manual_lamp_control=ctx.opts.manual_lamp_control)

        with hw.use_backlight(
            pars.METROLOGY_CAL_BACKLIGHT_VOLTAGE,
            manual_lamp_control=ctx.opts.manual_lamp_control,
        ):
            ipath_selftest_met_cal_fibre = capture_image(met_cal_cam, "met-cal-fibre")

        target_coordinates = metcalTargetCoordinates(
            ipath_selftest_met_cal_target, pars=MET_CAL_TARGET_ANALYSIS_PARS
        )
        fibre_coordinates = metcalFibreCoordinates(
            ipath_selftest_met_cal_fibre, pars=MET_CAL_FIBRE_ANALYSIS_PARS
        )

    finally:
        hw.safe_home_turntable(ctx.gd, ctx.grid_state)


def selftest_metrology_height(
    ctx, MET_HEIGHT_ANALYSIS_PARS=None, pars=None, capture_image=None
):

    print ("selftest: metrology height")
    if ctx.opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    try:
        hw.safe_home_turntable(ctx.gd, ctx.grid_state)

        hw.switch_fibre_backlight(
            "off", manual_lamp_control=ctx.opts.manual_lamp_control
        )
        hw.switch_ambientlight("off", manual_lamp_control=ctx.opts.manual_lamp_control)
        hw.switch_fibre_backlight_voltage(
            0.0, manual_lamp_control=ctx.opts.manual_lamp_control
        )

        MET_HEIGHT_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: MET_HEIGHT_CAMERA_IP_ADDRESS,
        }

        met_height_cam = hw.GigECamera(MET_HEIGHT_CAMERA_CONF)

        fpu_id, stage_position = get_sorted_positions(
            ctx.measure_fpuset, pars.MET_HEIGHT_POSITIONS
        )[0]

        # move rotary stage to POS_REP_POSN_N
        hw.turntable_safe_goto(ctx.gd, ctx.grid_state, stage_position)

        with hw.use_silhouettelight(manual_lamp_control=ctx.opts.manual_lamp_control):
            ipath_selftest_met_height = capture_image(
                met_height_cam, "metrology-height"
            )

        metht_small_target_height, metht_large_target_height = methtHeight(
            ipath_selftest_met_height, pars=MET_HEIGHT_ANALYSIS_PARS
        )

    finally:
        hw.safe_home_turntable(ctx.gd, ctx.grid_state)


def selftest_positional_repeatability(
    ctx, pars=None, POS_REP_ANALYSIS_PARS=None, capture_image=None
):

    print ("selftest: positional repeatability")

    if ctx.opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    try:
        hw.safe_home_turntable(ctx.gd, ctx.grid_state)

        hw.switch_fibre_backlight(
            "off", manual_lamp_control=ctx.opts.manual_lamp_control
        )
        hw.switch_fibre_backlight_voltage(
            0.0, manual_lamp_control=ctx.opts.manual_lamp_control
        )

        POS_REP_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: POS_REP_CAMERA_IP_ADDRESS,
        }

        pos_rep_cam = hw.GigECamera(POS_REP_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(pars.POS_REP_EXPOSURE_MS)

        fpu_id, stage_position = get_sorted_positions(
            ctx.measure_fpuset, pars.POS_REP_POSITIONS
        )[0]

        hw.turntable_safe_goto(ctx.gd, ctx.grid_state, stage_position)

        with hw.use_ambientlight(manual_lamp_control=ctx.opts.manual_lamp_control):

            selftest_ipath_pos_rep = capture_image(
                pos_rep_cam, "positional-repeatability"
            )

        coords = posrepCoordinates(selftest_ipath_pos_rep, pars=POS_REP_ANALYSIS_PARS)

    finally:
        hw.safe_home_turntable(ctx.gd, ctx.grid_state)


def selftest_nonfibre(
    ctx,
    MET_HEIGHT_ANALYSIS_PARS=None,
    MET_HEIGHT_MEASUREMENT_PARS=None,
    POS_REP_ANALYSIS_PARS=None,
    POS_REP_MEASUREMENT_PARS=None,
    PUP_ALGN_MEASUREMENT_PARS=None,
):

    print ("selftest: tests without fibre involved")

    tstamp = timestamp()

    def capture_image(cam, subtest):

        ipath = store_image(cam, "self-test/{ts}/{stest}.bmp", ts=tstamp, stest=subtest)
        return ipath

    try:
        selftest_metrology_height(
            ctx,
            MET_HEIGHT_ANALYSIS_PARS=MET_HEIGHT_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=MET_HEIGHT_MEASUREMENT_PARS,
        )

    # except Exception as e:
    except SystemError as e:
        print ("metrology height self-test failed", repr(e))
        sys.exit(1)

    try:
        selftest_positional_repeatability(
            ctx,
            POS_REP_ANALYSIS_PARS=POS_REP_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=POS_REP_MEASUREMENT_PARS,
        )
    except SystemError as e:
        print ("positional repeatability self-test failed", repr(e))
        sys.exit(1)
    print (">>>> selftest: tests without fibre succeeded")


def selftest_fibre(
    ctx,
    MET_CAL_MEASUREMENT_PARS=None,
    MET_CAL_FIBRE_ANALYSIS_PARS=None,
    MET_CAL_TARGET_ANALYSIS_PARS=None,
    PUP_ALGN_ANALYSIS_PARS=None,
    PUP_ALGN_MEASUREMENT_PARS=None,
):

    print ("selftest: tests requiring fibre")
    tstamp = timestamp()

    def capture_image(cam, subtest):

        ipath = store_image(cam, "self-test/{ts}/{stest}.bmp", ts=tstamp, stest=subtest)
        return ipath

    try:
        selftest_pup_algn(
            ctx,
            PUP_ALGN_ANALYSIS_PARS=PUP_ALGN_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=PUP_ALGN_MEASUREMENT_PARS,
        )

    except SystemError as e:
        print ("pupil alignment self-test failed:", repr(e))
        sys.exit(1)

    try:
        selftest_metrology_calibration(
            ctx,
            MET_CAL_TARGET_ANALYSIS_PARS=MET_CAL_TARGET_ANALYSIS_PARS,
            MET_CAL_FIBRE_ANALYSIS_PARS=MET_CAL_FIBRE_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=MET_CAL_MEASUREMENT_PARS,
        )
    except SystemError as e:
        print ("metrology calibration self-test failed", repr(e))
        sys.exit(1)

    print (">>>> selftest: tests requiring fibre succeeded")
