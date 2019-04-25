from __future__ import absolute_import, division, print_function

import warnings

from functools import partial

from fpu_commands import gen_wf
from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.base import get_min_quality
from ImageAnalysisFuncs.analyze_positional_repeatability import (
    DATUM_REPEATABILITY_ALGORITHM_VERSION,
    ImageAnalysisError,
    evaluate_datum_repeatability,
    posrepCoordinates,
)
from numpy import NaN, array
import numpy as np
from vfr.conf import MET_CAL_CAMERA_IP_ADDRESS
from vfr.db.base import TestResult
from vfr.db.datum_repeatability import (
    DatumRepeatabilityImages,
    DatumRepeatabilityResult,
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
    safe_home_turntable,
    turntable_safe_goto,
)


def check_skip(rig, dbe, fpu_id):
    """checks whether an FPU should be skipped because
    it was already tested. If so, return the reason as a string."""

    if get_datum_repeatability_passed_p(dbe, fpu_id) and (
        not rig.opts.repeat_passed_tests
    ):

        sn = rig.fpu_config[fpu_id]["serialnumber"]
        return "FPU %{} : datum repeatability test already passed, skipping test".format(
            sn
        )

    # no reason found, return a falsey value
    return None


def config_camera(rig, exposure_time):
    """configure the camera, returning a camera object."""

    # initialize camera
    # set camera exposure time to DATUM_REP_EXPOSURE milliseconds
    MET_CAL_CAMERA_CONF = {
        DEVICE_CLASS: BASLER_DEVICE_CLASS,
        IP_ADDRESS: MET_CAL_CAMERA_IP_ADDRESS,
    }

    met_cal_cam = rig.hw.GigECamera(MET_CAL_CAMERA_CONF)
    met_cal_cam.SetExposureTime(exposure_time)

    return met_cal_cam


def get_counter_residuals(rig, fpu_id):
    """get residual step countes for a specific FPU
    from the grid_state data structure.

    These residual values indicate when an FPU was missing
    steps during a movement, because normally
    the step numbers at dataum cancel out to zero.
    """

    rig.gd.getCounterDeviation(rig.grid_state, fpuset=[fpu_id])
    fpu = rig.grid_state.FPU[fpu_id]
    return (fpu.alpha_deviation, fpu.beta_deviation)


def move_then_datum(rig, fpu_id):
    """make a measurement where an FPU is first moved,
    then datumed, so that impact of movements on
    the FPUs mechanical precision is measured.
    """
    if rig.opts.verbosity > 0:
        print("moving FPU %i to (30,30) and back" % fpu_id)
    wf = gen_wf(30 * dirac(fpu_id, rig.opts.N), 30)
    verbosity = max(rig.opts.verbosity - 3, 0)
    gd = rig.gd
    grid_state = rig.grid_state

    gd.configMotion(wf, grid_state, verbosity=verbosity)
    gd.executeMotion(grid_state, fpuset=[fpu_id])
    gd.reverseMotion(grid_state, fpuset=[fpu_id], verbosity=verbosity)
    gd.executeMotion(grid_state, fpuset=[fpu_id])
    gd.findDatum(grid_state, fpuset=[fpu_id])


def grab_datumed_images(rig, fpu_id, capture_func, iterations):
    """perform a number of datum operations, store
    an image after each, and return the path names
    of the images, together with the residual count."""

    datumed_images = []
    datumed_residuals = []
    for count in range(iterations):

        print("capturing datumed-%02i" % count)

        rig.gd.findDatum(rig.grid_state, fpuset=[fpu_id])

        ipath = capture_func("datumed", count)
        datumed_images.append(ipath)

        alpha_dev, beta_dev = get_counter_residuals(rig, fpu_id)
        datumed_residuals.append((alpha_dev, beta_dev))

    return datumed_images, datumed_residuals


def grab_moved_images(rig, fpu_id, capture_func, iterations):
    """perform datum operations after moving, grab and
    collect images, and return resulting images and residual counts.
    """

    rig.gd.findDatum(rig.grid_state)
    moved_images = []
    moved_residuals = []
    for count in range(iterations):
        move_then_datum(rig, fpu_id)

        print("capturing moved+datumed-%02i" % count)
        ipath = capture_func("moved+datumed", count)
        moved_images.append(ipath)

        alpha_dev, beta_dev = get_counter_residuals(rig, fpu_id)
        moved_residuals.append((alpha_dev, beta_dev))

    return moved_images, moved_residuals


def record_images_from_fpu(rig, fpu_id, capture_image, num_iterations):
    """make a mesaurement series for a specific FPU."""

    sn = rig.fpu_config[fpu_id]["serialnumber"]
    capture_for_sn = partial(capture_image, sn)

    # capture images with datum-only hardware command
    datumed_images, datumed_residuals = grab_datumed_images(
        rig, fpu_id, capture_for_sn, num_iterations
    )

    # capture images whith FPU moveing, then datum
    moved_images, moved_residuals = grab_moved_images(
        rig, fpu_id, capture_for_sn, num_iterations
    )

    # wrap up the gathered data in a DB record
    image_record = DatumRepeatabilityImages(
        images={"datumed_images": datumed_images, "moved_images": moved_images},
        residual_counts={
            "datumed_residuals": datumed_residuals,
            "moved_residuals": moved_residuals,
        },
    )

    return image_record


def measure_datum_repeatability(rig, dbe, pars=None):
    # go to defined start configuration
    safe_home_turntable(rig, rig.grid_state)
    rig.lctrl.switch_all_off()

    with rig.lctrl.use_ambientlight():

        tstamp = timestamp()
        camera = config_camera(rig, pars.DATUM_REP_EXPOSURE_MS)

        # define closure which stores images with unique path names
        # (using time stamp and camera object configured above)
        def capture_image(sn, subtest, cnt):
            ipath = store_image(
                camera,
                "{sn}/{tn}/{ts}/{tp}-{ct:03d}.bmp",
                sn=sn,
                tn="datum-repeatability",
                ts=tstamp,
                tp=subtest,
                ct=cnt,
            )

            return ipath

        # turn table along sorted positions
        for fpu_id, stage_position in get_sorted_positions(
            rig.measure_fpuset, pars.DATUM_REP_POSITIONS
        ):

            skip_reason = check_skip(rig, dbe, fpu_id)
            if skip_reason:
                print(skip_reason)
                continue

            # move rotary stage to measurement position
            turntable_safe_goto(rig, rig.grid_state, stage_position)
            # measure images
            image_record = record_images_from_fpu(
                rig, fpu_id, capture_image, pars.DATUM_REP_ITERATIONS
            )
            # store to database
            save_datum_repeatability_images(dbe, fpu_id, image_record)


def eval_datum_repeatability(dbe, dat_rep_analysis_pars):

    for fpu_id in dbe.eval_fpuset:
        measurement = get_datum_repeatability_images(dbe, fpu_id)
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
            max_residual_datumed = np.max(array(residual_counts["datumed_residuals"]))
            max_residual_moved = np.max(array(residual_counts["moved_residuals"]))

            min_quality_datumed = get_min_quality(datumed_coords)

            min_quality_moved = get_min_quality(moved_coords)

        except ImageAnalysisError as e:
            errmsg = str(e)
            coords = {}
            datrep_dat_only_max = (
                datrep_dat_only_std
            ) = datrep_move_dat_max = datrep_move_dat_std = NaN

            datum_repeatability_has_passed = TestResult.NA
            max_residual_datumed = NaN
            max_residual_moved = NaN
            min_quality_datumed = NaN
            min_quality_moved = NaN
            datumed_errors = None
            moved_errors = None

            if dat_rep_analysis_pars.FIXME_FAKE_RESULT:
                warnings.warn(
                    "Faking passed result for datum repeatability "
                    "- does not work because test images is missing"
                )
                datum_repeatability_has_passed = TestResult.OK

        record = DatumRepeatabilityResult(
            algorithm_version=DATUM_REPEATABILITY_ALGORITHM_VERSION,
            coords=coords,
            datum_repeatability_max_residual_datumed=max_residual_datumed,
            datum_repeatability_max_residual_moved=max_residual_moved,
            datum_repeatability_move_max_mm=datrep_move_dat_max,
            datum_repeatability_move_std_mm=datrep_move_dat_std,
            datum_repeatability_only_max_mm=datrep_dat_only_max,
            datum_repeatability_only_std_mm=datrep_dat_only_std,
            datumed_errors=datumed_errors,
            error_message=errmsg,
            min_quality_datumed=min_quality_datumed,
            min_quality_moved=min_quality_moved,
            moved_errors=moved_errors,
            pass_threshold_mm=dat_rep_analysis_pars.DATUM_REP_PASS,
            result=datum_repeatability_has_passed,
        )

        save_datum_repeatability_result(dbe, fpu_id, record)
