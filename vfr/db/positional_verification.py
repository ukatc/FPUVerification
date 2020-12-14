from __future__ import absolute_import, division, print_function

from collections import namedtuple
from functools import partial
from vfr.db.base import TestResult, save_named_record, get_named_record, upgrade_version

import numpy as np

RECORD_TYPE = "positional-verification"

PositionalVerificationImages = namedtuple(
    "PositionalVerificationImages",
    " images"
    " gearbox_correction"
    " gearbox_algorithm_version"
    " gearbox_git_version"
    " gearbox_record_count"
    " calibration_mapfile"
    " datum_images",
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
    " measured_points"
    " expected_points"
    " mean_error_vector"
    " algorithm_version"
    " evaluation_version"
    " center_x"
    " center_y"
    " camera_offset"
    " datum_results",
)


save_positional_verification_images = partial(
    save_named_record, (RECORD_TYPE, "images"), include_fpu_id=True
)

DEFAULT_IMAGES_RECORD = {
    "datum_images" : []
}
get_positional_verification_images = partial(get_named_record, (RECORD_TYPE, "images"), default_vals=DEFAULT_IMAGES_RECORD)

save_positional_verification_result = partial(
    save_named_record, (RECORD_TYPE, "result")
)

upgrade_func = partial(upgrade_version, fieldname="algorithm_version")

DEFAULT_RECORD = {
    "expected_points" : [],
    "measured_points" : [],
    "mean_error_vector" : [np.NaN, np.NaN],
    "evaluation_version" : (0, 1, 0),
    "center_x" : np.NaN,
    "center_y" : np.NaN,
    "camera_offset" : np.NaN,
    "datum_results" : []
}

get_positional_verification_result = partial(
    get_named_record, (RECORD_TYPE, "result"), upgrade_func=upgrade_func, default_vals=DEFAULT_RECORD,
)


def get_positional_verification_passed_p(dbe, fpu_id, count=None):
    """returns True if the latest positional verification test for this
    FPU was passed successfully.

    """

    val = get_positional_verification_result(dbe, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
