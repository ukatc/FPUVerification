from __future__ import print_function, division

from numpy import NaN

import warnings
from vfr.conf import MET_CAL_CAMERA_IP_ADDRESS

from vfr.db.datum_repeatability import (
    TestResult,
    save_datum_repeatability_images,
    get_datum_repeatability_images,
    save_datum_repeatability_result,
    get_datum_repeatability_result,
    get_datum_repeatability_passed_p,
)


from vfr import hw
from vfr import hwsimulation


from GigE.GigECamera import DEVICE_CLASS, BASLER_DEVICE_CLASS, IP_ADDRESS


from fpu_commands import gen_wf


from vfr.tests_common import (
    timestamp,
    dirac,
    goto_position,
    find_datum,
    store_image,
    get_sorted_positions,
)


from ImageAnalysisFuncs.analyze_positional_repeatability import (
    ImageAnalysisError,
    posrepCoordinates,
    evaluate_datum_repeatability,
    DATUM_REPEATABILITY_ALGORITHM_VERSION,
)


def measure_datum_repeatability(ctx, pars=None):

    tstamp = timestamp()
    if ctx.opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    # home turntable
    hw.safe_home_turntable(ctx.gd, ctx.grid_state)

    hw.switch_fibre_backlight("off", manual_lamp_control=ctx.opts.manual_lamp_control)
    hw.switch_fibre_backlight_voltage(
        0.0, manual_lamp_control=ctx.opts.manual_lamp_control
    )

    with hw.use_ambientlight(manual_lamp_control=ctx.opts.manual_lamp_control):

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(
            ctx.measure_fpuset, pars.DATUM_REP_POSITIONS
        ):

            if get_datum_repeatability_passed_p(ctx, fpu_id) and (
                not ctx.opts.repeat_passed_tests
            ):

                sn = ctx.fpu_config[fpu_id]["serialnumber"]
                print (
                    "FPU %s : datum repeatability test already passed, skipping test"
                    % sn
                )
                continue

            # move rotary stage to POS_REP_POSN_N
            hw.turntable_safe_goto(ctx.gd, ctx.grid_state, stage_position)

            # initialize pos_rep camera
            # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
            MET_CAL_CAMERA_CONF = {
                DEVICE_CLASS: BASLER_DEVICE_CLASS,
                IP_ADDRESS: MET_CAL_CAMERA_IP_ADDRESS,
            }

            met_cal_cam = hw.GigECamera(MET_CAL_CAMERA_CONF)
            met_cal_cam.SetExposureTime(pars.DATUM_REP_EXPOSURE_MS)

            datumed_images = []
            moved_images = []

            def capture_image(subtest, cnt):

                ipath = store_image(
                    met_cal_cam,
                    "{sn}/{tn}/{ts}/{tp}-{ct:03d}.bmp",
                    sn=ctx.fpu_config[fpu_id]["serialnumber"],
                    tn="datum-repeatability",
                    ts=tstamp,
                    tp=subtest,
                    ct=cnt,
                )

                return ipath

            for count in range(pars.DATUM_REP_ITERATIONS):
                print("capturing datumed-%02i" % count)
                ctx.gd.findDatum(ctx.grid_state, fpuset=[fpu_id])
                ipath = capture_image("datumed", count)
                datumed_images.append(ipath)

            ctx.gd.findDatum(ctx.grid_state)
            for count in range(pars.DATUM_REP_ITERATIONS):
                print("capturing moved+datumed-%02i" % count)
                wf = gen_wf(30 * dirac(fpu_id, ctx.opts.N), 30)
                ctx.gd.configMotion(wf, ctx.grid_state)
                ctx.gd.executeMotion(ctx.grid_state, fpuset=[fpu_id])
                ctx.gd.reverseMotion(ctx.grid_state, fpuset=[fpu_id])
                ctx.gd.executeMotion(ctx.grid_state, fpuset=[fpu_id])
                ctx.gd.findDatum(ctx.grid_state, fpuset=[fpu_id])
                ipath = capture_image("moved+datumed", count)
                moved_images.append(ipath)

            images = {"datumed_images": datumed_images, "moved_images": moved_images}

            save_datum_repeatability_images(ctx, fpu_id, images)


def eval_datum_repeatability(ctx, dat_rep_analysis_pars):

    for fpu_id in ctx.eval_fpuset:
        images = get_datum_repeatability_images(ctx, fpu_id)["images"]

        def analysis_func(ipath):
            return posrepCoordinates(ipath, pars=dat_rep_analysis_pars)

        try:

            datumed_coords = map(analysis_func, images["datumed_images"])
            moved_coords = map(analysis_func, images["moved_images"])

            datum_repeatability_mm = evaluate_datum_repeatability(
                datumed_coords, moved_coords
            )

            datum_repeatability_has_passed = (
                TestResult.OK
                if datum_repeatability_mm <= DATUM_REP_PASS
                else TestResult.FAILED
            )

            coords = {"datumed_coords": datumed_coords, "moved_coords": moved_coords}
            errmsg = ""

        except ImageAnalysisError as e:
            errmsg = str(e)
            coords = {}
            datum_repeatability_mm = NaN
            datum_repeatability_has_passed = TestResult.NA

            if dat_rep_analysis_pars.FIXME_FAKE_RESULT:
                warnings.warn("Faking passed result for datum repeatability "
                              "- does not work because test images is missing")
                datum_repeatability_has_passed = TestResult.OK

        save_datum_repeatability_result(
            ctx,
            fpu_id,
            coords=coords,
            datum_repeatability_mm=datum_repeatability_mm,
            datum_repeatability_has_passed=datum_repeatability_has_passed,
            errmsg=errmsg,
            analysis_version=DATUM_REPEATABILITY_ALGORITHM_VERSION,
        )
