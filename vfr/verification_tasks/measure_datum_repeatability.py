from __future__ import absolute_import, division, print_function

import warnings

from fpu_commands import gen_wf
from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.analyze_positional_repeatability import (
    DATUM_REPEATABILITY_ALGORITHM_VERSION,
    ImageAnalysisError,
    evaluate_datum_repeatability,
    posrepCoordinates,
)
from numpy import NaN, array
import numpy as np
from vfr.conf import MET_CAL_CAMERA_IP_ADDRESS
from vfr.db.datum_repeatability import (
    TestResult,
    get_datum_repeatability_images,
    get_datum_repeatability_passed_p,
    save_datum_repeatability_images,
    save_datum_repeatability_result,
)
from vfr.tests_common import (
    dirac,
    get_sorted_positions,
    store_image,
    timestamp,
)


def measure_datum_repeatability(ctx, pars=None):

    tstamp = timestamp()

    # home turntable
    ctx.hw.safe_home_turntable(ctx.gd, ctx.grid_state)

    ctx.lctrl.switch_fibre_backlight("off", manual_lamp_control=ctx.opts.manual_lamp_control)
    ctx.lctrl.switch_fibre_backlight_voltage(
        0.0, manual_lamp_control=ctx.opts.manual_lamp_control
    )

    with ctx.lctrl.use_ambientlight(manual_lamp_control=ctx.opts.manual_lamp_control):

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(
            ctx.measure_fpuset, pars.DATUM_REP_POSITIONS
        ):

            if get_datum_repeatability_passed_p(ctx, fpu_id) and (
                not ctx.opts.repeat_passed_tests
            ):

                sn = ctx.fpu_config[fpu_id]["serialnumber"]
                print(
                    "FPU %s : datum repeatability test already passed, skipping test"
                    % sn
                )
                continue

            # move rotary stage to POS_REP_POSN_N
            ctx.hw.turntable_safe_goto(ctx.gd, ctx.grid_state, stage_position)

            # initialize pos_rep camera
            # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
            MET_CAL_CAMERA_CONF = {
                DEVICE_CLASS: BASLER_DEVICE_CLASS,
                IP_ADDRESS: MET_CAL_CAMERA_IP_ADDRESS,
            }

            met_cal_cam = ctx.hw.GigECamera(MET_CAL_CAMERA_CONF)
            met_cal_cam.SetExposureTime(pars.DATUM_REP_EXPOSURE_MS)

            datumed_images = []
            moved_images = []
            datumed_residuals = []
            moved_residuals = []

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
                ctx.gd.getCounterDeviation(ctx.grid_state, fpuset=[fpu_id])
                fpu = ctx.grid_state.FPU[fpu_id]
                datumed_residuals.append( (fpu.alpha_deviation, fpu.beta_deviation,) )


            ctx.gd.findDatum(ctx.grid_state)
            for count in range(pars.DATUM_REP_ITERATIONS):
                if ctx.opts.verbosity > 0:
                    print("moving FPU %i to (30,30) and back" % fpu_id)
                wf = gen_wf(30 * dirac(fpu_id, ctx.opts.N), 30)
                verbosity = max(ctx.opts.verbosity - 3, 0)
                gd = ctx.gd
                grid_state = ctx.grid_state

                gd.configMotion(wf, grid_state, verbosity=verbosity)
                gd.executeMotion(grid_state, fpuset=[fpu_id])
                gd.reverseMotion(grid_state, fpuset=[fpu_id], verbosity=verbosity)
                gd.executeMotion(grid_state, fpuset=[fpu_id])
                gd.findDatum(grid_state, fpuset=[fpu_id])
                print("capturing moved+datumed-%02i" % count)
                ipath = capture_image("moved+datumed", count)
                moved_images.append(ipath)

                ctx.gd.getCounterDeviation(ctx.grid_state, fpuset=[fpu_id])
                fpu = ctx.grid_state.FPU[fpu_id]
                moved_residuals.append( (fpu.alpha_deviation, fpu.beta_deviation,) )

            images = {"datumed_images": datumed_images, "moved_images": moved_images}
            residuals = {"datumed_residuals": datumed_residuals, "moved_residuals": moved_residuals}

            save_datum_repeatability_images(ctx, fpu_id, images, residuals)


def eval_datum_repeatability(ctx, dat_rep_analysis_pars):

    for fpu_id in ctx.eval_fpuset:
        measurement = get_datum_repeatability_images(ctx, fpu_id)
        if measurement is None:
            print("FPU %s: no datum repeatability measurement data found" % fpu_id)
            continue

        images = measurement["images"]

        residual_counts = measurement["residual_counts"]

        def analysis_func(ipath):
            return posrepCoordinates(ipath, pars=dat_rep_analysis_pars)

        try:

            datumed_coords = map(analysis_func, images["datumed_images"])
            moved_coords = map(analysis_func, images["moved_images"])

            (
                datrep_dat_only_max,
                datrep_dat_only_std,
                datrep_move_dat_max,
                datrep_move_dat_std,
                datumed_errors,
                moved_errors,
            ) = evaluate_datum_repeatability(datumed_coords, moved_coords)

            datum_repeatability_has_passed = (
                TestResult.OK
                if (
                    max(datrep_dat_only_max, datrep_move_dat_max)
                    <= dat_rep_analysis_pars.DATUM_REP_PASS
                )
                else TestResult.FAILED
            )

            coords = {"datumed_coords": datumed_coords, "moved_coords": moved_coords}
            errmsg = ""
            max_residual_datumed=np.max(array(residual_counts["datumed_residuals"]))
            max_residual_moved=np.max(array(residual_counts["moved_residuals"]))

        except ImageAnalysisError as e:
            errmsg = str(e)
            coords = {}
            datrep_dat_only_max = (
                datrep_dat_only_std
            ) = datrep_move_dat_max = datrep_move_dat_std = NaN

            datum_repeatability_has_passed = TestResult.NA
            max_residual_datumed=NaN
            max_residual_moved=NaN
            datumed_errors=None
            moved_errors = None


            if dat_rep_analysis_pars.FIXME_FAKE_RESULT:
                warnings.warn(
                    "Faking passed result for datum repeatability "
                    "- does not work because test images is missing"
                )
                datum_repeatability_has_passed = TestResult.OK

        save_datum_repeatability_result(
            ctx,
            fpu_id,
            coords=coords,
            datum_repeatability_only_max_mm=datrep_dat_only_max,
            datum_repeatability_only_std_mm=datrep_dat_only_std,
            datum_repeatability_move_max_mm=datrep_move_dat_max,
            datum_repeatability_move_std_mm=datrep_move_dat_std,
            datumed_errors=datumed_errors,
            moved_errors=moved_errors,
            max_residual_datumed=max_residual_datumed,
            max_residual_moved=max_residual_moved,
            datum_repeatability_has_passed=datum_repeatability_has_passed,
            pass_threshold_mm=dat_rep_analysis_pars.DATUM_REP_PASS,
            errmsg=errmsg,
            algorithm_version=DATUM_REPEATABILITY_ALGORITHM_VERSION,
        )
