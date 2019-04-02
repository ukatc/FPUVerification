from __future__ import absolute_import, division, print_function

from collections import namedtuple
from numpy import NaN
from vfr.tests_common import timestamp
from vfr.db.base import GIT_VERSION, get_test_result, save_test_result

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


def save_metrology_calibration_images(dbe, fpu_id, record):

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


def get_metrology_calibration_images(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "images")
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)


def save_metrology_calibration_result(dbe, fpu_id, record):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    def valfunc(fpu_id):

        val = dict(**vars(record))
        val.update({"git_version": GIT_VERSION, "time": timestamp()})
        return repr(val)

    save_test_result(dbe, [fpu_id], keyfunc, valfunc)


def get_metrology_calibration_result(dbe, fpu_id, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    return get_test_result(
        dbe, fpu_id, keyfunc, verbosity=dbe.opts.verbosity, count=count
    )
