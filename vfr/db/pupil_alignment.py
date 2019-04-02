from __future__ import absolute_import, division, print_function

from collections import namedtuple
from functools import partial
from vfr.tests_common import timestamp
from vfr.db.base import (TestResult,
                         save_named_record,
                         get_named_record,
                         get_test_result,
                         save_test_result,
)

RECORD_TYPE = "pupil-alignment"

PupilAlignmentImages = namedtuple("PupilAlignmentImages", " images")

PupilAlignmentResult = namedtuple(
    "PupilAlignmentResult",
    " calibration_pars"
    " coords"
    " measures"
    " result"
    " min_quality"
    " pass_threshold_mm"
    " error_message"
    " algorithm_version",
)


def save_pupil_alignment_images(dbe, fpu_id, record):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    def valfunc(fpu_id):

        val = dict(**vars(record))
        val.update({"fpuid": fpu_id, "time": timestamp()})
        return repr(val)

    save_test_result(dbe, [fpu_id], keyfunc, valfunc)


def get_pupil_alignment_images(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)


save_pupil_alignment_result = partial(save_named_record, (RECORD_TYPE, "result"))

get_pupil_alignment_result = partial(get_named_record, (RECORD_TYPE, "result"))

def get_pupil_alignment_passed_p(dbe, fpu_id, count=None):
    """returns True if the latest datum repeatability test for this FPU
    was passed successfully."""

    val = get_pupil_alignment_result(dbe, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
