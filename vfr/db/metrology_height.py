from __future__ import absolute_import, division, print_function

from collections import namedtuple
from functools import partial
from vfr.db.base import save_named_record, get_named_record, upgrade_version

RECORD_TYPE = "metrology-height"

MetrologyHeightImages = namedtuple("MetrologyHeightImages", " images")

MetrologyHeightResult = namedtuple(
    "MetrologyHeightResult",
    " small_target_height_mm"
    " large_target_height_mm"
    " test_result"
    " error_message"
    " algorithm_version",
)


save_metrology_height_images = partial(
    save_named_record, (RECORD_TYPE, "images"), include_fpu_id=True
)

get_metrology_height_images = partial(get_named_record, (RECORD_TYPE, "images"))

save_metrology_height_result = partial(save_named_record, (RECORD_TYPE, "result"))

upgrade_func = partial(upgrade_version, fieldname="algorithm_version")

get_metrology_height_result = partial(get_named_record, (RECORD_TYPE, "result"), upgrade_func=upgrade_func)
