from __future__ import absolute_import, division, print_function

from collections import namedtuple
from functools import partial
from vfr.db.base import TestResult, save_named_record, get_named_record, upgrade_version


RECORD_TYPE = "positional-verification"

PositionalVerificationImages = namedtuple(
    "PositionalVerificationImages",
    " images"
    " gearbox_correction"
    " gearbox_algorithm_version"
    " gearbox_git_version"
    " gearbox_record_count"
    " calibration_mapfile",
)

PositionalVerificationResult = namedtuple(
    "PositionalVerificationResult",
    " calibration_pars"
    " analysis_results"
    " posver_error_by_angle"
    " posver_error_measures"
    " result"
    " pass_threshold_mm"
    " min_quality"
    " arg_max_error"
    " error_message"
    " algorithm_version",
)


save_positional_verification_images = partial(
    save_named_record, (RECORD_TYPE, "images"), include_fpu_id=True
)

get_positional_verification_images = partial(get_named_record, (RECORD_TYPE, "images"))

save_positional_verification_result = partial(
    save_named_record, (RECORD_TYPE, "result")
)

upgrade_func = partial(upgrade_version, fieldname="algorithm_version")

get_positional_verification_result = partial(
    get_named_record, (RECORD_TYPE, "result"), upgrade_func=upgrade_func
)


def get_positional_verification_passed_p(dbe, fpu_id, count=None):
    """returns True if the latest positional verification test for this
    FPU was passed successfully.

    """

    val = get_positional_verification_result(dbe, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
