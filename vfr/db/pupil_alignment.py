from __future__ import absolute_import, division, print_function

from numpy import NaN
from vfr.tests_common import timestamp
from vfr.db.base import (
    GIT_VERSION,
    TestResult,
    get_test_result,
    save_test_result,
)

RECORD_TYPE = "pupil-alignment"


def save_pupil_alignment_images(dbe, fpu_id, images=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    def valfunc(fpu_id):

        val = repr({"fpuid": fpu_id, "images": images, "time": timestamp()})
        return val

    save_test_result(dbe, [fpu_id], keyfunc, valfunc)


def get_pupil_alignment_images(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)


def save_pupil_alignment_result(
    dbe,
    fpu_id,
    calibration_pars=None,
    coords=None,
    pupil_alignment_has_passed=None,
    pupil_alignment_measures=None,
    pass_threshold_mm=NaN,
    min_quality=NaN,
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
                "calibration_pars": calibration_pars,
                "coords": coords,
                "measures": pupil_alignment_measures,
                "result": pupil_alignment_has_passed,
                "min_quality" : min_quality,
                "pass_threshold_mm": pass_threshold_mm,
                "error_message": errmsg,
                "algorithm_version": algorithm_version,
                "git_version": GIT_VERSION,
                "time": timestamp(),
            }
        )
        return val

    save_test_result(dbe, [fpu_id], keyfunc, valfunc)


def get_pupil_alignment_result(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)


def get_pupil_alignment_passed_p(dbe, fpu_id, count=None):
    """returns True if the latest datum repeatability test for this FPU
    was passed successfully."""

    val = get_pupil_alignment_result(dbe, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
