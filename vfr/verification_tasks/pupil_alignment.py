from __future__ import absolute_import, division, print_function

from GigE.GigECamera import BASLER_DEVICE_CLASS, DEVICE_CLASS, IP_ADDRESS
from ImageAnalysisFuncs.analyze_pupil_alignment import (
    PUPIL_ALIGNMENT_ALGORITHM_VERSION,
    ImageAnalysisError,
    evaluate_pupil_alignment,
    get_min_quality_pupil,
    pupalnCoordinates,
)
from numpy import NaN
from vfr.conf import PUP_ALGN_CAMERA_IP_ADDRESS
from vfr.db.base import TestResult
from vfr.db.colldect_limits import get_range_limits
from vfr.db.pupil_alignment import (
    PupilAlignmentImages,
    PupilAlignmentResult,
    get_pupil_alignment_images,
    get_pupil_alignment_passed_p,
    save_pupil_alignment_images,
    save_pupil_alignment_result,
)
from vfr.tests_common import (
    find_datum,
    get_config_from_mapfile,
    get_sorted_positions,
    goto_position,
    store_image,
    timestamp,
)


def generate_positions():
    a0 = -170.0
    b0 = -170.0
    delta_a = 90.0
    delta_b = 90.0
    for j in range(4):
        for k in range(4):
            yield (a0 + delta_a * j, b0 + delta_b * k), True
    a_near = -179.0
    b_near = 1.0

    yield (a_near, b_near), False


def measure_pupil_alignment(rig, dbe, pars=None):

    tstamp = timestamp()

    if rig.opts.skip_fibre:
        print("option '--skip-fibre' is set -- skipping pupil alignment test")
        return

    # home turntable
    rig.hw.safe_home_turntable(rig, rig.grid_state)
    rig.hw.home_linear_stage()
    rig.lctrl.switch_all_off()

    with rig.lctrl.use_backlight(pars.PUP_ALGN_LAMP_VOLTAGE):

        # initialize pos_rep camera
        # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
        PUP_ALGN_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: PUP_ALGN_CAMERA_IP_ADDRESS,
        }

        pup_aln_cam = rig.hw.GigECamera(PUP_ALGN_CAMERA_CONF)
        pup_aln_cam.SetExposureTime(pars.PUP_ALGN_EXPOSURE_MS)

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(
            rig.measure_fpuset, pars.PUP_ALGN_POSITIONS
        ):

            if get_pupil_alignment_passed_p(dbe, fpu_id) and (
                not rig.opts.repeat_passed_tests
            ):

                sn = rig.fpu_config[fpu_id]["serialnumber"]
                print(
                    "FPU %s : pupil alignment test already passed,"
                    " skipping test for this FPU" % sn
                )
                continue

            range_limits = get_range_limits(dbe, rig, fpu_id)
            if range_limits is None:
                print("FPU %s : limit test value missing, skipping test" % sn)
                continue

            if ((range_limits.alpha_min > -170.0)
                or (range_limits.beta_min > -170.0)
                or (range_limits.alpha_max < +100.0)
                or (range_limits.beta_max < +100.0)):
                print("FPU %s : range limits insufficient for pupil alignment test,"
                      " skipping test" % sn)
                continue



            # move rotary stage to PUP_ALGN_POSN_N
            rig.hw.turntable_safe_goto(rig, rig.grid_state, stage_position)
            rig.hw.linear_stage_goto(pars.PUP_ALGN_LINPOSITIONS[fpu_id])

            sn = rig.fpu_config[fpu_id]["serialnumber"]

            def capture_image(count, alpha, beta):

                ipath = store_image(
                    pup_aln_cam,
                    "{sn}/{tn}/{ts}/{cnt:02d}-{alpha:+08.3f}-{beta:+08.3f}.bmp",
                    sn=sn,
                    tn="pupil-alignment",
                    ts=tstamp,
                    cnt=count,
                    alpha=alpha,
                    beta=beta,
                )

                return ipath

            images = {}
            for count, (coords, do_capture) in enumerate(generate_positions()):
                abs_alpha, abs_beta = coords
                if rig.opts.verbosity > 3:
                    print(
                        "FPU %s: go to position (%7.2f, %7.2f)"
                        % (sn, abs_alpha, abs_beta)
                    )

                goto_position(
                    rig.gd, abs_alpha, abs_beta, rig.grid_state, fpuset=[fpu_id]
                )

                if do_capture:
                    if rig.opts.verbosity > 0:
                        print(
                            "FPU %s: saving image for (%7.2f, %7.2f)"
                            % (sn, abs_alpha, abs_beta)
                        )
                    ipath = capture_image(count, abs_alpha, abs_beta)
                    images[(abs_alpha, abs_beta)] = ipath

            find_datum(rig.gd, rig.grid_state, rig.opts)

            record = PupilAlignmentImages(
                images=images, calibration_mapfile=pars.PUP_ALGN_CALIBRATION_MAPFILE
            )
            save_pupil_alignment_images(dbe, fpu_id, record)

    rig.hw.home_linear_stage()  # bring linear stage to home pos


def eval_pupil_alignment(
    dbe, PUP_ALGN_ANALYSIS_PARS=None, PUP_ALGN_EVALUATION_PARS=None
):

    for fpu_id in dbe.eval_fpuset:
        measurement = get_pupil_alignment_images(dbe, fpu_id)

        if measurement is None:
            print("FPU %s: no pupil alignment measurement data found" % fpu_id)
            continue

        images = measurement["images"]

        mapfile = measurement["calibration_mapfile"]
        USE_MAPFILE = False # False because we do not yet have a
                            # working calibration - delete this when
                            # it's fixed
        if mapfile and USE_MAPFILE:
            # this is a temporary solution because ultimately we want to
            # pass a function reference to calibrate points, because that's
            # more efficient.
            PUP_ALGN_ANALYSIS_PARS.PUP_ALGN_CALIBRATION_PARS = get_config_from_mapfile(mapfile)

        def analysis_func(ipath):
            return pupalnCoordinates(ipath, pars=PUP_ALGN_ANALYSIS_PARS)

        try:
            coords = dict((k, analysis_func(v)) for k, v in images.items())

            pupalnChassisErr, pupalnAlphaErr, pupalnBetaErr, pupalnTotalErr, pupalnErrorBars = evaluate_pupil_alignment(
                coords, pars=PUP_ALGN_EVALUATION_PARS
            )

            pupil_alignment_has_passed = (
                TestResult.OK
                if pupalnTotalErr <= PUP_ALGN_EVALUATION_PARS.PUP_ALGN_PASS
                else TestResult.FAILED
            )

            errmsg = ""

            min_quality = get_min_quality_pupil(coords.values())

        except ImageAnalysisError as e:
            errmsg = str(e)
            coords = {}
            pupalnChassisErr = NaN
            pupalnAlphaErr = NaN
            pupalnBetaErr = NaN
            pupalnTotalErr = NaN
            pupil_alignment_has_passed = TestResult.NA
            min_quality = NaN

        pupil_alignment_measures = {
            "chassis_error": pupalnChassisErr,
            "alpha_error": pupalnAlphaErr,
            "beta_error": pupalnBetaErr,
            "total_error": pupalnTotalErr,
        }

        record = PupilAlignmentResult(
            calibration_pars=PUP_ALGN_ANALYSIS_PARS.PUP_ALGN_CALIBRATION_PARS,
            coords=coords,
            measures=pupil_alignment_measures,
            result=pupil_alignment_has_passed,
            min_quality=min_quality,
            pass_threshold_mm=PUP_ALGN_EVALUATION_PARS.PUP_ALGN_PASS,
            error_message=errmsg,
            algorithm_version=PUPIL_ALIGNMENT_ALGORITHM_VERSION,
        )
        save_pupil_alignment_result(dbe, fpu_id, record)
