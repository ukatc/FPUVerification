from __future__ import print_function, division, absolute_import

from vfr.db.base import GIT_VERSION, TestResult, get_test_result, timestamp


def save_angular_limit(
    ctx, fpu_id, serialnumber, which_limit, test_succeeded, limit_val, diagnostic
):

    print ("saving limit value")

    def keyfunc(fpu_id):
        if which_limit == "beta_collision":
            keybase = (serialnumber, which_limit)
        else:
            keybase = (serialnumber, "limit", which_limit)
        return keybase

    def valfunc(fpu_id):

        if test_succeeded:
            fsuccess = TestResult.OK
        else:
            fsuccess = TestResult.FAILED

        val = repr(
            {
                "result": fsuccess,
                "val": limit_val,
                "diagnostic": diagnostic,
                "time": timestamp(),
            }
        )
        return val

    save_test_result(ctx, [fpu_id], keyfunc, valfunc)


def get_angular_limit(ctx, fpu_id, serialnumber, which_limit):
    def keyfunc(fpu_id):
        if which_limit == "beta_collision":
            keybase = (serialnumber, which_limit)
        else:
            keybase = (serialnumber, "limit", which_limit)
        return keybase

    return get_test_result(ctx, [fpu_id], keyfunc)


def get_anglimit_passed_p(ctx, fpu_id, serialnumber, which_limit):

    result = get_angular_limit(ctx, fpu_id, serialnumber, which_limit)

    if result is None:
        return False
    return result["result"] == TestResult.OK


def get_colldect_passed_p(ctx, fpu_id, serialnumber):
    return get_anglimit_passed_p(ctx, fpu_id, serialnumber, "beta_collision")


def set_protection_limit(ctx, fpu_id, which_limit, measured_val):

    """This replaces the corresponding entry in the protection database if
    either the update flag is True, or the current entry is the default value.
    """
    if which_limit in ["alpha_max", "alpha_min"]:
        subkey = pdb.alpha_limits
        offset = ALPHA_DATUM_OFFSET
        default_min, default_max = ALPHA_MIN_DEGREE, ALPHA_MAX_DEGREE
    else:
        subkey = pdb.beta_limits
        offset = 0.0
        default_min, default_max = BETA_MIN_DEGREE, BETA_MAX_DEGREE

    is_min = which_limit in ["beta_min", "alpha_min"]

    if is_min:
        default_val = default_min
    else:
        default_val = default_max

    fpu = ctx.grid_state.FPU[fpu_id]
    serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
    with ctx.env.begin(write=True, db=ctx.fpudb) as txn:
        val = pdb.getField(txn, fpu, subkey) + offset

        val_min = val.min()
        val_max = val.max()
        if is_min:
            if (val_min == default_val) or ctx.opts.update:
                val_min = measured_val + protection_tolerance
        else:
            if (val_max == default_val) or ctx.opts.update:
                val_max = measured_val - protection_tolerance

        new_val = Interval(val_min, val_max)
        print ("limit %s: replacing %r by %r" % (which_limit, val, new_val))
        pdb.putInterval(txn, serialnumber, subkey, new_val, offset)
