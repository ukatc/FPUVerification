from __future__ import absolute_import, division, print_function

from collections import namedtuple
from functools import partial
from vfr.db.base import TestResult, save_named_record, get_named_record, upgrade_version

RECORD_TYPE = "positional-repeatability"

PositionalRepeatabilityImages = namedtuple(
    "PositionalRepeatabilityImages",
    " images_alpha" " images_beta" " waveform_pars" " calibration_mapfile",
)

PositionalRepeatabilityResults = namedtuple(
    "PositionalRepeatabilityResults",
    " calibration_pars"
    " analysis_results_alpha"
    " analysis_results_beta"
    " posrep_alpha_max_at_angle"
    " posrep_beta_max_at_angle"
    " arg_max_alpha_error"
    " arg_max_beta_error"
    " min_quality_alpha"
    " min_quality_beta"
    " posrep_alpha_measures"
    " posrep_beta_measures"
    " result"
    " pass_threshold_mm"
    " gearbox_correction"
    " error_message"
    " algorithm_version"
    " gearbox_correction_version",
)


save_positional_repeatability_images = partial(
    save_named_record, (RECORD_TYPE, "images"), include_fpu_id=True
)

get_positional_repeatability_images = partial(get_named_record, (RECORD_TYPE, "images"))

save_positional_repeatability_result = partial(
    save_named_record, (RECORD_TYPE, "result")
)

# convert version from float format to 3-tuple, using semantic versioning
upgrade_func1 = partial(upgrade_version, fieldname="algorithm_version")
upgrade_func2 = partial(upgrade_version, fieldname="gearbox_correction_version")

def upgrade_func(x):
    return upgrade_func2(upgrade_func1(x))

default_vals = {
    "gearbox_correction_version" : (0, 1, 0),
}

get_positional_repeatability_result = partial(get_named_record, (RECORD_TYPE, "result"),
                                              upgrade_func=upgrade_func,
                                              default_vals=default_vals,
)


def get_positional_repeatability_passed_p(dbe, fpu_id, count=None):
    """returns True if the latest positional repeatability test for this FPU
    was passed successfully."""

    val = get_positional_repeatability_result(dbe, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
