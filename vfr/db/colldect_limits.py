from __future__ import absolute_import, division, print_function

from collections import namedtuple
from numpy import isnan

from fpu_constants import (
    ALPHA_MAX_DEGREE,
    ALPHA_MIN_DEGREE,
    BETA_MAX_DEGREE,
    BETA_MIN_DEGREE,
)
from interval import Interval
from protectiondb import ProtectionDB
from vfr.conf import PROTECTION_TOLERANCE, ALPHA_RANGE_MAX, ALPHA_DATUM_OFFSET
from vfr.tests_common import timestamp
from vfr.db.base import TestResult, get_test_result, save_test_result

LimitTestResult = namedtuple(
    "LimitTestResult",
    " fpu_id" " serialnumber" " result" " val" " diagnostic" " limit_name",
)


def save_angular_limit(dbe, which_limit, record):

    if dbe.opts.verbosity > 3:
        print("saving limit value")

    serialnumber = record.serialnumber
    fpu_id = record.fpu_id

    def keyfunc(fpu_id):
        if which_limit == "beta_collision":
            keybase = (serialnumber, which_limit)
        else:
            keybase = (serialnumber, "limit", which_limit)
        return keybase

    def valfunc(fpu_id):

        val = dict(**vars(record))
        val.update({"time": timestamp()})
        return repr(val)

    save_test_result(dbe, [fpu_id], keyfunc, valfunc)


def get_angular_limit(dbe, fpu_id, which_limit, count=None):

    serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]

    def keyfunc(fpu_id):
        if which_limit == "beta_collision":
            keybase = (serialnumber, which_limit)
        else:
            keybase = (serialnumber, "limit", which_limit)
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)


def get_anglimit_passed_p(dbe, fpu_id, which_limit, count=None):

    result = get_angular_limit(dbe, fpu_id, which_limit, count=count)

    if result is None:
        return False
    return result["result"] == TestResult.OK


def get_colldect_passed_p(dbe, fpu_id, count=None):
    return get_anglimit_passed_p(dbe, fpu_id, "beta_collision", count=count)


def set_protection_limit(dbe, grid_state, which_limit, record):

    """This replaces the corresponding entry in the protection database if
    either the update flag is True, or the current entry is the default value.
    """
    fpu_id = record.fpu_id
    measured_val = record.val
    serialnumber = record.serialnumber

    if which_limit in ["alpha_max", "alpha_min"]:
        subkey = ProtectionDB.alpha_limits
        offset = ALPHA_DATUM_OFFSET
        default_min, default_max = ALPHA_MIN_DEGREE, ALPHA_MAX_DEGREE
    else:
        subkey = ProtectionDB.beta_limits
        offset = 0.0
        default_min, default_max = BETA_MIN_DEGREE, BETA_MAX_DEGREE

    is_min = which_limit in ["beta_min", "alpha_min"]

    if is_min:
        default_val = default_min
    else:
        default_val = default_max

    fpu = grid_state.FPU[fpu_id]

    with dbe.env.begin(write=True, db=dbe.fpudb) as txn:
        val = ProtectionDB.getField(txn, fpu, subkey) + offset

        val_min = val.min()
        val_max = val.max()
        if is_min:
            if (val_min == default_val) or dbe.opts.update_protection_limits:
                val_min = measured_val + PROTECTION_TOLERANCE
        else:
            if (val_max == default_val) or dbe.opts.update_protection_limits:
                val_max = measured_val - PROTECTION_TOLERANCE

        new_val = Interval(val_min, val_max)
        print("limit %s: replacing %r by %r" % (which_limit, val, new_val))
        ProtectionDB.putInterval(txn, serialnumber, subkey, new_val, offset)


RangeLimits = namedtuple(
    "RangeLimits", " alpha_min" " alpha_max" " beta_min" " beta_max"
)


def get_range_limits(dbe, rig, fpu_id):
    # get measured limits (in case of alpha limit, assume a fixed
    # value until it can be measured with upgraded FPU firmware).
    _alpha_min = get_angular_limit(dbe, fpu_id, "alpha_min")
    if _alpha_min is None:
        _alpha_min = {"val": ALPHA_DATUM_OFFSET}

    _alpha_max = get_angular_limit(dbe, fpu_id, "alpha_max")
    if _alpha_max is None:
        _alpha_max = {"val": ALPHA_RANGE_MAX}
    _beta_min = get_angular_limit(dbe, fpu_id, "beta_min")
    _beta_max = get_angular_limit(dbe, fpu_id, "beta_max")

    if (
        (_alpha_min is None)
        or (_alpha_max is None)
        or (_beta_min is None)
        or (_beta_max is None)
    ):
        return None

    alpha_min = _alpha_min["val"]
    alpha_max = _alpha_max["val"]
    beta_min = _beta_min["val"]
    beta_max = _beta_max["val"]



    # Get protection intervals from protection database
    fpu = rig.grid_state.FPU[fpu_id]
    with dbe.env.begin(db=dbe.fpudb) as txn:
        interval_alpha = ProtectionDB.getField(txn, fpu, ProtectionDB.alpha_limits) + ALPHA_DATUM_OFFSET
        interval_beta = ProtectionDB.getField(txn, fpu, ProtectionDB.beta_limits)

    # If needed, reduce measured or assumed limits to FPU driver
    # protection limits. The driver would block any FPU movement
    # exceeding these, causing the verification run to fail.
    alpha_min = max(alpha_min, interval_alpha.min())
    alpha_max = min(alpha_max, interval_alpha.max())

    beta_min = max(beta_min, interval_beta.min())
    beta_max = min(beta_max, interval_beta.max())


    assert not isnan(alpha_min)
    assert not isnan(alpha_max)
    assert not isnan(beta_min)
    assert not isnan(beta_max)

    limits = RangeLimits(
        alpha_min=alpha_min, alpha_max=alpha_max, beta_min=beta_min, beta_max=beta_max
    )
    return limits
