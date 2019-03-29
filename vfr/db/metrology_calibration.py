from __future__ import absolute_import, division, print_function

from numpy import NaN
from vfr.db.base import (
    GIT_VERSION,
    TestResult,
    get_test_result,
    save_test_result,
    timestamp,
)

RECORD_TYPE = "metrology-calibration"


def save_metrology_calibration_images(ctx, fpu_id, images):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    def valfunc(fpu_id):

        val = repr({"fpuid": fpu_id, "images": images, "time": timestamp()})
        return val

    save_test_result(ctx, [fpu_id], keyfunc, valfunc)


def get_metrology_calibration_images(ctx, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    return get_test_result(ctx, fpu_id, keyfunc, count=count)


def save_metrology_calibration_result(
    ctx,
    fpu_id,
    coords=None,
    metcal_fibre_large_target_distance_mm=NaN,
    metcal_fibre_small_target_distance_mm=NaN,
    metcal_target_vector_angle_deg=NaN,
    errmsg="",
    algorithm_version=None,
):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    def valfunc(fpu_id):

        val = repr(
            {
                "coords": coords,
                "metcal_fibre_large_target_distance_mm": metcal_fibre_large_target_distance_mm,
                "metcal_fibre_small_target_distance_mm": metcal_fibre_small_target_distance_mm,
                "metcal_target_vector_angle_deg": metcal_target_vector_angle_deg,
                "error_message": errmsg,
                "algorithm_version": algorithm_version,
                "git_version": GIT_VERSION,
                "time": timestamp(),
            }
        )
        return val

    save_test_result(ctx, [fpu_id], keyfunc, valfunc)


def get_metrology_calibration_result(ctx, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    return get_test_result(
        ctx, fpu_id, keyfunc, verbosity=ctx.opts.verbosity, count=count
    )
