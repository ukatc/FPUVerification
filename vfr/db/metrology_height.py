from __future__ import absolute_import, division, print_function

from collections import namedtuple
from functools import partial
from vfr.tests_common import timestamp
from vfr.db.base import (save_named_record,
                         get_named_record,
                         get_test_result,
                         save_test_result,
)

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


def save_metrology_height_images(dbe, fpu_id, record):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    def valfunc(fpu_id):
        val = dict(**vars(record))
        val.update({"fpu_id": fpu_id, "time": timestamp()})
        return repr(val)

    save_test_result(dbe, [fpu_id], keyfunc, valfunc)


def get_metrology_height_images(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)

save_metrology_height_result = partial(save_named_record, (RECORD_TYPE, "result"))

get_metrology_height_result = partial(get_named_record, (RECORD_TYPE, "result"))
