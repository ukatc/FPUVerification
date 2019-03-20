from __future__ import print_function, division, absolute_import

from vfr.db.base import GIT_VERSION, TestResult, save_test_result, get_test_result, timestamp

RECORD_TYPE = "positional-repeatability"


def save_positional_repeatability_images(
    ctx, fpu_id, images_dict_alpha=None, images_dict_beta=None, waveform_pars={}
):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    def valfunc(fpu_id):

        val = repr(
            {
                "fpuid": fpu_id,
                "images_alpha": image_dict_alpha,
                "images_beta": image_dict_beta,
                "waveform_pars": waveform_pars,
                "time": timestamp(),
            }
        )
        return val

    save_test_result(ctx, [fpu_id], keyfunc, valfunc)


def get_positional_repeatability_images(ctx, fpu_id):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    return get_test_result(ctx, fpu_id, keyfunc)


def save_positional_repeatability_result(
    ctx,
    fpu_id,
    pos_rep_calibration_pars=None,
    analysis_results_alpha=None,
    analysis_results_beta=None,
    positional_repeatability_mm=None,
    gearbox_correction={},
    analysis_version=None,
    errmsg="",
    positional_repeatability_has_passed=None,
):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    def valfunc(fpu_id):

        val = repr(
            {
                "calibration_pars": pos_rep_calibration_pars,
                "analysis_results_alpha": analysis_results_alpha,
                "analysis_results_beta": analysis_results_beta,
                "repeatability_millimeter": positional_repeatability_mm,
                "result": positional_repeatability_has_passed,
                "gearbox_correction": gearbox_correction,
                "error_message": errmsg,
                "algorithm_version": analysis_version,
                "git-version": GIT_VERSION,
                "time": timestamp(),
            }
        )
        return val

    save_test_result(ctx, [fpu_id], keyfunc, valfunc)


def get_positional_repeatability_result(ctx, fpu_id):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    return get_test_result(ctx, fpu_id, keyfunc)


def get_positional_repeatability_passed_p(ctx, fpu_id):
    """returns True if the latest positional repeatability test for this FPU
    was passed successfully."""

    val = get_positional_repeatability_result(ctx, fpu_id)

    if val is None:
        return False

    return val["result"] == TestResult.OK
