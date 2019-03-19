from __future__ import print_function, division, absolute_import

from vfr.db.base import GIT_VERSION, TestResult, get_test_result, timestamp


def save_positional_verification_images(ctx, fpu_id, images_dict):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, "positional-verification", "images")
        return keybase

    def valfunc(fpu_id):

        val = repr({"fpuid": fpu_id, "images": image_dict, "time": timestamp()})
        return val

    save_test_result(ctx, [fpu_id], keyfunc, valfunc)


def get_positional_verification_images(ctx, fpu_id):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, "positional-verification", "images")
        return keybase

    return get_test_result(ctx, [fpu_id], keyfunc)


def save_positional_verification_result(
    ctx,
    fpu_id,
    pos_rep_calibration_pars=None,
    analysis_results=None,
    posver_errors=None,
    positional_verification_mm=None,
    errmsg="",
    analysis_version=None,
    positional_verification_has_passed=None,
):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, "positional-verification", "result")
        return keybase

    def valfunc(fpu_id):

        val = repr(
            {
                "calibration_pars": pos_rep_calibration_pars,
                "analysis_results": analysis_results,
                "verification_millimeter": positional_verification_mm,
                "result": positional_verification_has_passed,
                "posver_errors": posver_errors,
                "error_message": errmsg,
                "algorithm_version": analysis_version,
                "git-version": GIT_VERSION,
                "algorithm_version": analysis_version,
                "time": timestamp(),
            }
        )
        return val

    save_test_result(ctx, [fpu_id], keyfunc, valfunc)


def get_positional_verification_result(ctx, fpu_id):
    def keyfunc(fpu_id):
        serialnumber = fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, "positional-verification", "result")
        return keybase

    return get_test_result(ctx, [fpu_id], keyfunc)
