from __future__ import print_function, division

from numpy import NaN

from vfr.conf import PUP_ALN_CAMERA_IP_ADDRESS

from vfr.db.pupil_alignment import (
    TestResult,
    save_pupil_alignment_images,
    get_pupil_alignment_images,
    save_pupil_alignment_result,
    get_pupil_alignment_result,
    get_pupil_alignment_passed_p,
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
    PUPIL_ALIGNMENT_ALGORITHM_VERSION,
)


def generate_positions():
    a0 = -170.0
    b0 = -170.0
    delta_a = 90.0
    delta_b = 90.0
    for j in range(4):
        for k in range(4):
            yield (a0 + delta_a * j, b0 + delta_b * k)
    a_near = 1.0
    b_near = 1.0

    yield (ALPHA_DATUM_OFFSET + a_near, 0 + b_near)


def measure_pupil_alignment(
    env,
    vfdb,
    gd,
    grid_state,
    opts,
    fpuset,
    fpu_config,
    PUPIL_ALN_POSITIONS=None,
    PUPIL_ALN_LINPOSITIONS=None,
    PUPIL_ALN_EXPOSURE_MS=None,
):

    tstamp = timestamp()

    if opts.mockup:
        # replace all hardware functions by mock-up interfaces
        hw = hwsimulation

    # home turntable
    hw.safe_home_turntable(gd, grid_state)
    hw.home_linear_stage()

    hw.switch_ambientlight("off", manual_lamp_control=opts.manual_lamp_control)
    hw.switch_silhouettelight("off", manual_lamp_control=opts.manual_lamp_control)
    hw.switch_fibre_backlight_voltage(5.0, manual_lamp_control=opts.manual_lamp_control)

    with hw.use_backlight("on", manual_lamp_control=opts.manual_lamp_control):

        # initialize pos_rep camera
        # set pos_rep camera exposure time to DATUM_REP_EXPOSURE milliseconds
        PUP_ALN_CAMERA_CONF = {
            DEVICE_CLASS: BASLER_DEVICE_CLASS,
            IP_ADDRESS: PUP_ALN_CAMERA_IP_ADDRESS,
        }

        pup_aln_cam = hw.GigECamera(PUP_ALN_CAMERA_CONF)
        pup_aln_cam.SetExposureTime(PUPIL_ALN_EXPOSURE_MS)

        # get sorted positions (this is needed because the turntable can only
        # move into one direction)
        for fpu_id, stage_position in get_sorted_positions(fpuset, PUP_ALN_POSITIONS):

            if get_pupil_alignment_passed_p(env, vfdb, opts, fpu_config, fpu_id) and (
                not opts.repeat_passed_tests
            ):

                sn = fpu_config[fpu_id]["serialnumber"]
                print (
                    "FPU %s : pupil alignment test already passed, skipping test" % sn
                )
                continue

            # move rotary stage to PUP_ALN_POSN_N
            hw.turntable_safe_goto(gd, grid_state, stage_position)
            hw.linear_stage__goto(PUPIL_ALN_LINPOSITIONS[fpu_id])

            def capture_image(count, alpha, beta):

                ipath = store_image(
                    pup_aln_cam,
                    "{sn}/{tn}/{ts}/{tp}-{cnt:02d}-{alpha:+08.3f}-{beta:+08.3f}.bmp",
                    sn=fpu_config[fpu_id]["serialnumber"],
                    tn="pupil-alignment",
                    ts=tstamp,
                    cnt=count,
                    alpha=alpha,
                    beta=beta,
                )

                return ipath

            images = {}
            for count, coords in enumerate(generate_positions()):
                abs_alpha, abs_beta = coords
                goto_position(gd, abs_alpha, abs_beta, grid_state, fpuset=[fpu_id])

                if count < 16:
                    ipath = capture_image(count, alpha, beta)
                    images[(alpha, beta)] = ipath

            gd.findDatum(grid_state, fpuset=[fpu_id])

            save_pupil_alignment_images(env, vfdb, opts, fpu_config, fpu_id, images)


def eval_pupil_alignment(
    env,
    vfdb,
    gd,
    grid_state,
    opts,
    fpuset,
    fpu_config,
    PUPALGN_CALIBRATION_PARS=None,
    PUPALGN_ANALYSIS_PARS=None,
    PUPIL_ALN_PASS=NaN,
):

    for fpu_id in fpuset:
        images = get_pupil_alignment_images(env, vfdb, opts, fpu_config, fpu_id, images)

        def analysis_func(ipath):
            return pupalnCoordinates(
                ipath,
                PUPALGN_CALIBRATION_PARS=PUPALGN_CALIBRATION_PARS,
                **PUPALGN_ANALYSIS_PARS
            )

        try:
            coords = dict((k, analysis_func(v)) for k, v in images.items())

            pupalnChassisErr, pupalnAlphaErr, pupalnBetaErr, pupalnTotalErr, pupalnErrorBars = evaluate_pupil_alignment(
                coords
            )

            pupil_alignment_has_passed = (
                TestResult.OK
                if pupil_alignment_mm <= PUPIL_ALN_PASS
                else TestResult.FAILED
            )

            errmsg = ""

        except ImageAnalysisError as e:
            errmsg = str(e)
            coords = {}
            pupalnChassisErr = pupalnAlphaErr = pupalnBetaErr = pupalnTotalErr = NaN
            pupil_alignment_has_passed = TestResult.NA

        pupil_alignment_measures = {
            "chassis_error": pupalnChassisErr,
            "alpha_error": pupalnAlphaErr,
            "beta_error": pupalnBetaErr,
            "total_error": pupalnTotalErr,
        }

        save_pupil_alignment_result(
            env,
            vfdb,
            opts,
            fpu_config,
            fpu_id,
            calibration_pars=PUPALGN_CALIBRATION_PARS,
            coords=coords,
            pupil_alignment_measures=pupil_alignment_measures,
            pupil_alignment_has_passed=datum_repeatability_has_passed,
            ermmsg=errmsg,
            analysis_version=PUPIL_ALIGNMENT_ALGORITHM_VERSION,
        )
