from __future__ import absolute_import, division, print_function

from collections import namedtuple
from functools import partial
from numpy import max
from vfr.tests_common import timestamp
from vfr.db.base import (TestResult,
                         save_named_record,
                         get_named_record,
                         get_test_result,
                         save_test_result,
)

RECORD_TYPE = "positional-repeatability"

PositionalRepeatabilityImages = namedtuple(
    "PositionalRepeatabilityImages", " images_alpha" " images_beta" " waveform_pars"
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
    " posrep_alpha_max_mm"
    " posrep_beta_max_mm"
    " posrep_rss_mm"
    " result"
    " pass_threshold_mm"
    " gearbox_correction"
    " error_message"
    " algorithm_version",
)


def save_positional_repeatability_images(dbe, fpu_id, record):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    def valfunc(fpu_id):

        val = dict(**vars(record))
        val.update({"fpuid": fpu_id, "time": timestamp()})
        return repr(val)

    verbosity = max(dbe.opts.verbosity - 4, 0)
    save_test_result(dbe, [fpu_id], keyfunc, valfunc, verbosity=verbosity)


def get_positional_repeatability_images(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    verbosity = max(dbe.opts.verbosity - 3, 0)
    return get_test_result(dbe, fpu_id, keyfunc, verbosity=verbosity, count=count)



save_positional_repeatability_result = partial(save_named_record, (RECORD_TYPE, "result"), verbosity_offset=3)

get_positional_repeatability_result = partial(get_named_record, (RECORD_TYPE, "result"), verbosity_offset=3)

def get_positional_repeatability_passed_p(dbe, fpu_id, count=None):
    """returns True if the latest positional repeatability test for this FPU
    was passed successfully."""

    val = get_positional_repeatability_result(dbe, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
