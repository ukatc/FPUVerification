from __future__ import absolute_import, division, print_function

from numpy import NaN

from vfr.db.base import (
    GIT_VERSION,
    TestResult,
    get_test_result,
    save_test_result,
    timestamp,
)

RECORD_TYPE = "positional-verification"

def save_positional_verification_images(ctx, fpu_id, image_dict=None, gearbox_correction=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    def valfunc(fpu_id):

        val = repr({
            "fpuid": fpu_id,
            "images": image_dict,
            "gearbox_correction" : gearbox_correction,
            "time": timestamp()})
        return val

    save_test_result(ctx, [fpu_id], keyfunc, valfunc)


def get_positional_verification_images(ctx, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    return get_test_result(ctx, fpu_id, keyfunc, count=count)


def save_positional_verification_result(
    ctx,
    fpu_id,
    pos_ver_calibration_pars=None,
    analysis_results=None,
    posver_error=[],
    posver_error_max=None,
    pass_threshold=NaN,
    errmsg="",
    analysis_version=None,
    positional_verification_has_passed=None,
):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    def valfunc(fpu_id):

        val = repr(
            {
                "calibration_pars": pos_ver_calibration_pars,
                "analysis_results": analysis_results,
                "posver_error" : posver_error,
                "posver_error_max" : posver_error_max,
                "result": positional_verification_has_passed,
                "pass_threshold": pass_threshold,
                "error_message": errmsg,
                "algorithm_version": analysis_version,
                "git-version": GIT_VERSION,
                "algorithm_version": analysis_version,
                "time": timestamp(),
            }
        )
        return val

    save_test_result(ctx, [fpu_id], keyfunc, valfunc)


def get_positional_verification_result(ctx, fpu_id, count=None):
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    return get_test_result(ctx, fpu_id, keyfunc, count=count)

def get_positional_verification_passed_p(ctx, fpu_id, count=None):
    """returns True if the latest positional verification test for this
    FPU was passed successfully.

    """

    val = get_positional_verification_result(ctx, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
