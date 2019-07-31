from __future__ import absolute_import, division, print_function

from collections import namedtuple
from functools import partial
from vfr.db.base import save_named_record, get_named_record, upgrade_version


RECORD_TYPE = "metrology-calibration"

MetrologyCalibrationImages = namedtuple("MetrologyCalibrationImages", " images")

MetrologyCalibrationResult = namedtuple(
    "MetrologyCalibrationResult",
    " coords"
    " metcal_fibre_large_target_distance_mm"
    " metcal_fibre_small_target_distance_mm"
    " metcal_target_vector_angle_deg"
    " error_message"
    " algorithm_version",
)


save_metrology_calibration_images = partial(
    save_named_record, (RECORD_TYPE, "images"), include_fpu_id=True
)

get_metrology_calibration_images = partial(get_named_record, (RECORD_TYPE, "images"))

save_metrology_calibration_result = partial(save_named_record, (RECORD_TYPE, "result"))

upgrade_func = partial(upgrade_version, fieldname="algorithm_version")

get_metrology_calibration_result = partial(get_named_record, (RECORD_TYPE, "result"), upgrade_func=upgrade_func)
