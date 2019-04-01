from __future__ import absolute_import, division, print_function

from vfr.tests_common import timestamp
from vfr.db.base import (
    GIT_VERSION,
    get_test_result,
    save_test_result,
)

RECORD_TYPE = "metrology-height"


def save_metrology_height_images(dbe, fpu_id, images):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    def valfunc(fpu_id):

        val = repr({"fpuid": fpu_id, "images": images, "time": timestamp()})
        return val

    save_test_result(dbe, [fpu_id], keyfunc, valfunc)


def get_metrology_height_images(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)


def save_metrology_height_result(
    dbe,
    fpu_id,
    metht_small_target_height_mm=None,
    metht_large_target_height_mm=None,
    test_result=None,
    errmsg="",
    algorithm_version=None,
):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    def valfunc(fpu_id):

        val = repr(
            {
                "small_target_height_mm": metht_small_target_height_mm,
                "large_target_height_mm": metht_large_target_height_mm,
                "test_result": test_result,
                "error_message": errmsg,
                "algorithm_version": algorithm_version,
                "git_version": GIT_VERSION,
                "time": timestamp(),
            }
        )
        return val

    save_test_result(dbe, [fpu_id], keyfunc, valfunc)


def get_metrology_height_result(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)
