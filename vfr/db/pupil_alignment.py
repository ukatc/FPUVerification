from __future__ import absolute_import, division, print_function

from collections import namedtuple
from functools import partial
from vfr.db.base import (TestResult,
                         save_named_record,
                         get_named_record,
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


save_pupil_alignment_images = partial(save_named_record, (RECORD_TYPE, "images"), include_fpu_id=True)

get_pupil_alignment_images = partial(get_named_record, (RECORD_TYPE, "images"))

save_pupil_alignment_result = partial(save_named_record, (RECORD_TYPE, "result"))

get_pupil_alignment_result = partial(get_named_record, (RECORD_TYPE, "result"))

def get_pupil_alignment_passed_p(dbe, fpu_id, count=None):
    """returns True if the latest datum repeatability test for this FPU
    was passed successfully."""

    val = get_pupil_alignment_result(dbe, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
