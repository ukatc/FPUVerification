from __future__ import absolute_import, division, print_function

from collections import namedtuple
from numpy import NaN
from vfr.tests_common import timestamp
from vfr.db.base import (
    GIT_VERSION,
    TestResult,
    get_test_result,
    save_test_result,
)

RECORD_TYPE = "datum-repeatability"

DatumRepeatabilityImages = namedtuple(
    "DatumRepeatabilityImages",
    " images"
    " residual_counts"
)

DatumRepeatabilityResult = namedtuple(
    "DatumRepeatabilityResult",
    " algorithm_version"
    " coords"
    " datum_repeatability_max_residual_datumed"
    " datum_repeatability_max_residual_moved"
    " datum_repeatability_move_max_mm"
    " datum_repeatability_move_std_mm"
    " datum_repeatability_only_max_mm"
    " datum_repeatability_only_std_mm"
    " datumed_errors"
    " error_message"
    " min_quality_datumed"
    " min_quality_moved"
    " moved_errors"
    " pass_threshold_mm"
    " result"
)



def save_datum_repeatability_images(dbe, fpu_id, record):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    def valfunc(fpu_id):

        val = dict(**vars(record))
        val.update({
            "fpuid": fpu_id,
            "time": timestamp()
        })
        return repr(val)

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
    record,
):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    def valfunc(fpu_id):

        val = dict(**vars(record))
        val.update({
                "git_version": GIT_VERSION,
                "time": timestamp(),
        })
        return repr(val)

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
