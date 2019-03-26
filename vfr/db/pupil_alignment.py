from __future__ import absolute_import, division, print_function

from numpy import NaN

from vfr.db.base import (
    GIT_VERSION,
    TestResult,
    get_test_result,
    save_test_result,
    timestamp,
)


RECORD_TYPE = "pupil-alignment"


def save_pupil_alignment_images(ctx, fpu_id, images=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    def valfunc(fpu_id):

        val = repr({"fpuid": fpu_id, "images": images, "time": timestamp()})
        return val

    save_test_result(ctx, [fpu_id], keyfunc, valfunc)


def get_pupil_alignment_images(ctx, fpu_id):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    return get_test_result(ctx, fpu_id, keyfunc)


def save_pupil_alignment_result(
    ctx,
    fpu_id,
    calibration_pars=None,
    coords=None,
    pupil_alignment_has_passed=None,
    pupil_alignment_measures=None,
    pass_threshold=NaN,
    errmsg="",
    analysis_version=None,
):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    def valfunc(fpu_id):

        val = repr(
            {
                "calibration_pars": calibration_pars,
                "coords": coords,
                "measures": pupil_alignment_measures,
                "result": pupil_alignment_has_passed,
                "pass_threshold" : pass_threshold,
                "error_message": errmsg,
                "git-version": GIT_VERSION,
                "time": timestamp(),
            }
        )
        return val

    save_test_result(ctx, [fpu_id], keyfunc, valfunc)


def get_pupil_alignment_result(ctx, fpu_id):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    return get_test_result(ctx, fpu_id, keyfunc)


def get_pupil_alignment_passed_p(ctx, fpu_id):
    """returns True if the latest datum repeatability test for this FPU
    was passed successfully."""

    val = get_pupil_alignment_result(ctx, fpu_id)

    if val is None:
        return False

    return val["result"] == TestResult.OK
