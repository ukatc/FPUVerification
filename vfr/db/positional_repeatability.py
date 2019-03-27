from __future__ import absolute_import, division, print_function

from numpy import NaN, max

from vfr.db.base import (
    GIT_VERSION,
    TestResult,
    get_test_result,
    save_test_result,
    timestamp,
)

RECORD_TYPE = "positional-repeatability"


def save_positional_repeatability_images(
    ctx, fpu_id, image_dict_alpha=None, image_dict_beta=None, waveform_pars={}
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

    verbosity = max(ctx.opts.verbosity - 4, 0)
    save_test_result(ctx, [fpu_id], keyfunc, valfunc, verbosity=verbosity)


def get_positional_repeatability_images(ctx, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    verbosity = max(ctx.opts.verbosity - 3, 0)
    return get_test_result(ctx, fpu_id, keyfunc, verbosity=verbosity, count=count)


def save_positional_repeatability_result(
    ctx,
    fpu_id,
    pos_rep_calibration_pars=None,
    analysis_results_alpha=None,
    analysis_results_beta=None,
    posrep_alpha_max_at_angle={},
    posrep_beta_max_at_angle={},
    posrep_alpha_max=NaN,
    posrep_beta_max=NaN,
    posrep_rss_mm=NaN,
    pass_threshold=NaN,
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
                "analysis_results_alpha" : analysis_results_alpha,
                "analysis_results_beta" : analysis_results_beta,
                "posrep_alpha_max_at_angle" : posrep_alpha_max_at_angle,
                "posrep_beta_max_at_angle" : posrep_beta_max_at_angle,
                "posrep_alpha_max" : posrep_alpha_max,
                "posrep_beta_max" : posrep_beta_max,
                "posrep_rss_mm" : posrep_rss_mm,
                "result": positional_repeatability_has_passed,
                "pass_threshold": pass_threshold,
                "gearbox_correction": gearbox_correction,
                "error_message": errmsg,
                "algorithm_version": analysis_version,
                "git-version": GIT_VERSION,
                "time": timestamp(),
            }
        )
        return val

    verbosity=max(ctx.opts.verbosity - 3, 0)
    if verbosity > 3:
        print("saving positional repetabilty result..")
    save_test_result(ctx, [fpu_id], keyfunc, valfunc, verbosity=verbosity)


def get_positional_repeatability_result(ctx, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    return get_test_result(ctx, fpu_id, keyfunc, count=count)


def get_positional_repeatability_passed_p(ctx, fpu_id, count=None):
    """returns True if the latest positional repeatability test for this FPU
    was passed successfully."""

    val = get_positional_repeatability_result(ctx, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
