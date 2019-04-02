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


RECORD_TYPE = "positional-verification"

PositionalVerificationImages = namedtuple(
    "PositionalVerificationImages",
    " images"
    " gearbox_correction"
    " gearbox_algorithm_version"
    " gearbox_git_version"
    " gearbox_record_count",
)

PositionalVerificationResult = namedtuple(
    "PositionalVerificationResult",
    " calibration_pars"
    " analysis_results"
    " posver_error"
    " posver_error_max_mm"
    " result"
    " pass_threshold_mm"
    " min_quality"
    " arg_max_error"
    " error_message"
    " algorithm_version",
)


def save_positional_verification_images(dbe, fpu_id, record):

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


def get_positional_verification_images(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)


save_positional_verification_result = partial(save_named_record, (RECORD_TYPE, "result"))

get_positional_verification_result = partial(get_named_record, (RECORD_TYPE, "result"))

def get_positional_verification_passed_p(dbe, fpu_id, count=None):
    """returns True if the latest positional verification test for this
    FPU was passed successfully.

    """

    val = get_positional_verification_result(dbe, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
