from __future__ import absolute_import, division, print_function

from collections import namedtuple
from functools import partial
from vfr.db.base import TestResult, save_named_record, get_named_record, upgrade_version

RECORD_TYPE = "datum-repeatability"

DatumRepeatabilityImages = namedtuple(
    "DatumRepeatabilityImages", " images" " residual_counts"
)

DatumRepeatabilityResult = namedtuple(
    "DatumRepeatabilityResult",
    " algorithm_version"
    " coords"
    " datum_repeatability_max_residual_datumed"
    " datum_repeatability_max_residual_moved"
    " datum_repeatability_datum_only"
    " datum_repeatability_moved"
    " datum_repeatability_combined"
    " error_message"
    " min_quality_datumed"
    " min_quality_moved"
    " pass_threshold_mm"
    " result",
)


save_datum_repeatability_images = partial(
    save_named_record, (RECORD_TYPE, "images"), include_fpu_id=True
)

get_datum_repeatability_images = partial(get_named_record, (RECORD_TYPE, "images"))

save_datum_repeatability_result = partial(save_named_record, (RECORD_TYPE, "result"))

upgrade_func = partial(upgrade_version, fieldname="algorithm_version")

get_datum_repeatability_result = partial(
    get_named_record, (RECORD_TYPE, "result"), upgrade_func=upgrade_func
)


def get_datum_repeatability_passed_p(dbe, fpu_id, count=None):
    """returns True if the latest datum repeatability test for this FPU
    was passed successfully."""

    val = get_datum_repeatability_result(dbe, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
