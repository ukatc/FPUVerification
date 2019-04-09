from __future__ import absolute_import, division, print_function

import sys
from warnings import warn

from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.base import ImageAnalysisError
from ImageAnalysisFuncs.analyze_metrology_calibration import (
    metcalFibreCoordinates,
    metcalTargetCoordinates,
)
from ImageAnalysisFuncs.analyze_metrology_height import methtHeight
from ImageAnalysisFuncs.analyze_positional_repeatability import posrepCoordinates
from ImageAnalysisFuncs.analyze_pupil_alignment import pupalnCoordinates
from vfr.conf import (
    MET_CAL_CAMERA_IP_ADDRESS,
    MET_HEIGHT_CAMERA_IP_ADDRESS,
    POS_REP_CAMERA_IP_ADDRESS,
    PUP_ALGN_CAMERA_IP_ADDRESS,
)
from vfr.tests_common import get_sorted_positions, store_image, timestamp


def selftest_pup_algn(rig, pars=None, PUP_ALGN_ANALYSIS_PARS=None, capture_image=None):
    print("selftest: pupil alignment")

    try:
        # home turntable
        rig.hw.safe_home_turntable(rig.gd, rig.grid_state)
        rig.hw.home_linear_stage()
        rig.lctrl.switch_all_off()

        with rig.lctrl.use_backlight(5.0):

            # initialize pos_rep camera
            # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
            PUP_ALGN_CAMERA_CONF = {
                DEVICE_CLASS: BASLER_DEVICE_CLASS,
                IP_ADDRESS: PUP_ALGN_CAMERA_IP_ADDRESS,
            }

            pup_aln_cam = rig.hw.GigECamera(PUP_ALGN_CAMERA_CONF)
            pup_aln_cam.SetExposureTime(pars.PUP_ALGN_EXPOSURE_MS)

            fpu_id, lin_position = get_sorted_positions(
                rig.measure_fpuset, pars.PUP_ALGN_POSITIONS
            )[0]

            stage_position = pars.PUP_ALGN_POSITIONS[fpu_id]

            # move rotary stage to PUP_ALN_POSN_N
            rig.hw.turntable_safe_goto(rig.gd, rig.grid_state, stage_position)
            rig.hw.linear_stage_goto(lin_position)

            ipath_selftest_pup_algn = capture_image(pup_aln_cam, "pupil-alignment")

            try:
                result = pupalnCoordinates(
                    ipath_selftest_pup_algn, pars=PUP_ALGN_ANALYSIS_PARS
                )
                del result
            except ImageAnalysisError as err:
                if rig.opts.ignore_analysis_failures:
                    warn("FAILED: self-test pupil alignment image"
                         " analysis (ignored), message = %s" % repr(err))
                else:
                    raise

    finally:
        rig.hw.safe_home_turntable(rig.gd, rig.grid_state)
        rig.hw.home_linear_stage()


def selftest_metrology_calibration(
    rig,
    pars=None,
    MET_CAL_TARGET_ANALYSIS_PARS=None,
    MET_CAL_FIBRE_ANALYSIS_PARS=None,
    capture_image=None,
):

    print("selftest: metrology calibration")

    try:
        # home turntable
        rig.hw.safe_home_turntable(rig.gd, rig.grid_state)
        rig.hw.home_linear_stage()
        rig.lctrl.switch_all_off()

        MET_CAL_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: MET_CAL_CAMERA_IP_ADDRESS,
        }

        met_cal_cam = rig.hw.GigECamera(MET_CAL_CAMERA_CONF)

        # get sorted positions (here, and only here, we use the linear
        # stage because it is much slower, so using the minimum linear
        # position accelerates the self-test)
        fpu_id, lin_position = get_sorted_positions(
            rig.measure_fpuset, pars.METROLOGY_CAL_LINPOSITIONS
        )[0]

        stage_position = pars.METROLOGY_CAL_POSITIONS[fpu_id]

        # move rotary stage to POS_REP_POSN_0
        rig.hw.turntable_safe_goto(rig.gd, rig.grid_state, stage_position)

        met_cal_cam.SetExposureTime(pars.METROLOGY_CAL_TARGET_EXPOSURE_MS)
        rig.lctrl.switch_all_off()

        # use context manager to switch lamp on
        # and guarantee it is switched off after the
        # measurement (even if exceptions occur)
        with rig.lctrl.use_ambientlight():
            ipath_selftest_met_cal_target = capture_image(met_cal_cam, "met-cal-target")

        met_cal_cam.SetExposureTime(pars.METROLOGY_CAL_FIBRE_EXPOSURE_MS)
        rig.hw.linear_stage_goto(lin_position)
        rig.lctrl.switch_all_off()

        with rig.lctrl.use_backlight(pars.METROLOGY_CAL_BACKLIGHT_VOLTAGE):
            ipath_selftest_met_cal_fibre = capture_image(met_cal_cam, "met-cal-fibre")

        try:
            target_coordinates = metcalTargetCoordinates(
                ipath_selftest_met_cal_target, pars=MET_CAL_TARGET_ANALYSIS_PARS
            )
            del target_coordinates
        except ImageAnalysisError as err:
            if rig.opts.ignore_analysis_failures:
                warn("FAILED: self-test metrology calibration image"
                     " analysis (ignored), message = %s" % repr(err))
            else:
                raise


        fibre_coordinates = metcalFibreCoordinates(
            ipath_selftest_met_cal_fibre, pars=MET_CAL_FIBRE_ANALYSIS_PARS
        )
        del fibre_coordinates

    finally:
        rig.hw.safe_home_turntable(rig.gd, rig.grid_state)


def selftest_metrology_height(
    rig, MET_HEIGHT_ANALYSIS_PARS=None, pars=None, capture_image=None
):

    print("selftest: metrology height")

    try:
        rig.hw.safe_home_turntable(rig.gd, rig.grid_state)
        rig.lctrl.switch_all_off()

        MET_HEIGHT_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: MET_HEIGHT_CAMERA_IP_ADDRESS,
        }

        met_height_cam = rig.hw.GigECamera(MET_HEIGHT_CAMERA_CONF)

        fpu_id, stage_position = get_sorted_positions(
            rig.measure_fpuset, pars.MET_HEIGHT_POSITIONS
        )[0]

        # move rotary stage to POS_REP_POSN_N
        rig.hw.turntable_safe_goto(rig.gd, rig.grid_state, stage_position)

        with rig.lctrl.use_silhouettelight():
            ipath_selftest_met_height = capture_image(
                met_height_cam, "metrology-height"
            )

        try:
            metht_small_target_height_mm, metht_large_target_height_mm = methtHeight(
                ipath_selftest_met_height, pars=MET_HEIGHT_ANALYSIS_PARS
            )
            del metht_small_target_height_mm
            del metht_large_target_height_mm

        except ImageAnalysisError as err:
            if rig.opts.ignore_analysis_failures:
                warn("FAILED: self-test metrology height image"
                     " analysis (ignored), message = %r" % repr(err))
            else:
                raise


    finally:
        rig.hw.safe_home_turntable(rig.gd, rig.grid_state)


def selftest_positional_repeatability(
    rig, pars=None, POS_REP_ANALYSIS_PARS=None, capture_image=None
):

    print("selftest: positional repeatability")

    try:
        rig.hw.safe_home_turntable(rig.gd, rig.grid_state)
        rig.lctrl.switch_all_off()

        POS_REP_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: POS_REP_CAMERA_IP_ADDRESS,
        }

        pos_rep_cam = rig.hw.GigECamera(POS_REP_CAMERA_CONF)
        pos_rep_cam.SetExposureTime(pars.POS_REP_EXPOSURE_MS)

        fpu_id, stage_position = get_sorted_positions(
            rig.measure_fpuset, pars.POS_REP_POSITIONS
        )[0]

        rig.hw.turntable_safe_goto(rig.gd, rig.grid_state, stage_position)

        with rig.lctrl.use_ambientlight():

            selftest_ipath_pos_rep = capture_image(
                pos_rep_cam, "positional-repeatability"
            )

        try:
            coords = posrepCoordinates(selftest_ipath_pos_rep, pars=POS_REP_ANALYSIS_PARS)
            del coords
        except ImageAnalysisError as err:
            if rig.opts.ignore_analysis_failures:
                warn("FAILED: self-test positional repeatability image"
                     " analysis (ignored), message = %r" % repr(err))
            else:
                raise

    finally:
        rig.hw.safe_home_turntable(rig.gd, rig.grid_state)


def selftest_nonfibre(
    rig,
    MET_HEIGHT_ANALYSIS_PARS=None,
    MET_HEIGHT_MEASUREMENT_PARS=None,
    POS_REP_ANALYSIS_PARS=None,
    POS_REP_MEASUREMENT_PARS=None,
    PUP_ALGN_MEASUREMENT_PARS=None,
):

    print("selftest: tests without fibre involved")

    tstamp = timestamp()

    def capture_image(cam, subtest):

        ipath = store_image(cam, "self-test/{ts}/{stest}.bmp", ts=tstamp, stest=subtest)
        return ipath

    try:
        selftest_metrology_height(
            rig,
            MET_HEIGHT_ANALYSIS_PARS=MET_HEIGHT_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=MET_HEIGHT_MEASUREMENT_PARS,
        )

    # except Exception as e:
    except SystemError as e:
        print("metrology height self-test failed", repr(e))
        sys.exit(1)

    try:
        selftest_positional_repeatability(
            rig,
            POS_REP_ANALYSIS_PARS=POS_REP_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=POS_REP_MEASUREMENT_PARS,
        )
    except SystemError as e:
        print("positional repeatability self-test failed", repr(e))
        sys.exit(1)
    print(">>>> selftest: tests without fibre succeeded")


def selftest_fibre(
    rig,
    MET_CAL_MEASUREMENT_PARS=None,
    MET_CAL_FIBRE_ANALYSIS_PARS=None,
    MET_CAL_TARGET_ANALYSIS_PARS=None,
    PUP_ALGN_ANALYSIS_PARS=None,
    PUP_ALGN_MEASUREMENT_PARS=None,
):

    print("selftest: tests requiring fibre")
    tstamp = timestamp()

    def capture_image(cam, subtest):

        ipath = store_image(cam, "self-test/{ts}/{stest}.bmp", ts=tstamp, stest=subtest)
        return ipath

    try:
        selftest_pup_algn(
            rig,
            PUP_ALGN_ANALYSIS_PARS=PUP_ALGN_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=PUP_ALGN_MEASUREMENT_PARS,
        )

    except SystemError as e:
        print("pupil alignment self-test failed:", repr(e))
        sys.exit(1)

    try:
        selftest_metrology_calibration(
            rig,
            MET_CAL_TARGET_ANALYSIS_PARS=MET_CAL_TARGET_ANALYSIS_PARS,
            MET_CAL_FIBRE_ANALYSIS_PARS=MET_CAL_FIBRE_ANALYSIS_PARS,
            capture_image=capture_image,
            pars=MET_CAL_MEASUREMENT_PARS,
        )
    except SystemError as e:
        print("metrology calibration self-test failed", repr(e))
        sys.exit(1)

    print(">>>> selftest: tests requiring fibre succeeded")
