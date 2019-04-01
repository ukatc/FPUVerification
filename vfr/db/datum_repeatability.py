from __future__ import absolute_import, division, print_function

from numpy import NaN
from vfr.tests_common import timestamp
from vfr.db.base import (
    GIT_VERSION,
    TestResult,
    get_test_result,
    save_test_result,
)

RECORD_TYPE = "datum-repeatability"


def save_datum_repeatability_images(dbe, fpu_id, images, residuals):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    def valfunc(fpu_id):

        val = repr({
            "fpuid": fpu_id,
            "images": images,
            "residual_counts" : residuals,
            "time": timestamp()
        })
        return val

    save_test_result(dbe, [fpu_id], keyfunc, valfunc)


def get_datum_repeatability_images(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)


def save_datum_repeatability_result(
    dbe,
    fpu_id,
    coords=None,
    datum_repeatability_only_max_mm=None,
    datum_repeatability_only_std_mm=None,
    datum_repeatability_move_max_mm=None,
    datum_repeatability_move_std_mm=None,
    datum_repeatability_has_passed=None,
    datumed_errors=None,
    moved_errors=None,
    max_residual_datumed=NaN,
    max_residual_moved=NaN,
    pass_threshold_mm=NaN,
    errmsg="",
    algorithm_version=None,
):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    def valfunc(fpu_id):

        val = repr(
            {
                "coords": coords,
                "datum_repeatability_only_max_mm": datum_repeatability_only_max_mm,
                "datum_repeatability_only_std_mm": datum_repeatability_only_std_mm,
                "datum_repeatability_move_max_mm": datum_repeatability_move_max_mm,
                "datum_repeatability_move_std_mm": datum_repeatability_move_std_mm,
                "datum_repeatability_max_residual_datumed" : max_residual_datumed,
                "datum_repeatability_max_residual_moved" : max_residual_moved,
                "datumed_errors" : datumed_errors,
                "moved_errors" : moved_errors,
                "result": datum_repeatability_has_passed,
                "pass_threshold_mm": pass_threshold_mm,
                "error_message": errmsg,
                "git_version": GIT_VERSION,
                "algorithm_version": algorithm_version,
                "time": timestamp(),
            }
        )
        return val

    save_test_result(dbe, [fpu_id], keyfunc, valfunc)


def get_datum_repeatability_result(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)


def get_datum_repeatability_passed_p(dbe, fpu_id, count=None):
    """returns True if the latest datum repeatability test for this FPU
    was passed successfully."""

    val = get_datum_repeatability_result(dbe, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
