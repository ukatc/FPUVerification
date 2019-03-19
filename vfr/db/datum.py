from __future__ import print_function, division, absolute_import

from vfr.db.base import GIT_VERSION, TestResult, get_test_result, timestamp
from vfr.db.snset import add_sns_to_set

RECORD_TYPE = "findDatum"


def save_datum_result(ctx, dasel, rigstate):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, str(dasel))
        return keybase

    def valfunc(fpu_id):

        if CAN_PROTOCOL_VERSION == 1:
            a_ok = ctx.grid_state.FPU[fpu_id].alpha_was_zeroed
            b_ok = ctx.grid_state.FPU[fpu_id].beta_was_zeroed
        else:
            a_ok = ctx.grid_state.FPU[fpu_id].alpha_was_calibrated
            b_ok = ctx.grid_state.FPU[fpu_id].beta_was_calibrated

        print ("%i : (alpha datumed=%s, beta datumed = %s)" % (fpu_id, a_ok, b_ok))

        if (
            ((dasel == DASEL_ALPHA) and a_ok)
            or ((dasel == DASEL_BETA) and b_ok)
            or ((dasel == DASEL_BOTH) and a_ok and b_ok)
        ):

            fsuccess = TestResult.OK
        else:
            fsuccess = TestResult.FAILED

        fpu = ctx.grid_state.FPU[fpu_id]
        val = repr(
            {
                "result": fsuccess,
                "datumed": (a_ok, b_ok),
                "fpuid": fpu_id,
                "counter_deviation": (fpu.alpha_deviation, fpu.alpha_deviation),
                "result_state": str(fpu.state),
                "diagnostic": "OK" if fsuccess else rigstate,
                "time": timestamp(),
            }
        )
        return val

    save_test_result(ctx, ctx.measure_fpuset, keyfunc, valfunc)
    # we update the set of FPUs which are in the database,
    # so that we can iterate over existing data when generating reports.
    add_sns_to_set(ctx, ctx.measure_fpuset)


def get_datum_result(ctx, fpu_id):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = ctx.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, "result")
        return keybase

    return get_test_result(ctx, [fpu_id], keyfunc, verbosity=opts.verbosity)


def get_datum_passed_p(ctx, fpu_id):
    """returns True if the latest datum repeatability test for this FPU
    was passed successfully."""

    val = get_datum_result(ctx, fpu_id)

    if val is None:
        return False

    return val["result"] == TestResult.OK
