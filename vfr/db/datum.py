from __future__ import absolute_import, division, print_function

from FpuGridDriver import CAN_PROTOCOL_VERSION, DASEL_ALPHA, DASEL_BETA, DASEL_BOTH
from vfr.tests_common import timestamp
from vfr.db.base import TestResult, get_test_result, save_test_result

RECORD_TYPE = "findDatum"


def save_datum_result(rig, dbe, dasel, rigstate):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, str(dasel))
        return keybase

    def valfunc(fpu_id):

        if CAN_PROTOCOL_VERSION == 1:
            a_ok = rig.grid_state.FPU[fpu_id].alpha_was_zeroed
            b_ok = rig.grid_state.FPU[fpu_id].beta_was_zeroed
        else:
            a_ok = rig.grid_state.FPU[fpu_id].alpha_was_calibrated
            b_ok = rig.grid_state.FPU[fpu_id].beta_was_calibrated

        print("%i : (alpha datumed=%s, beta datumed = %s)" % (fpu_id, a_ok, b_ok))

        if (
            ((dasel == DASEL_ALPHA) and a_ok)
            or ((dasel == DASEL_BETA) and b_ok)
            or ((dasel == DASEL_BOTH) and a_ok and b_ok)
        ):

            fsuccess = TestResult.OK
        else:
            fsuccess = TestResult.FAILED

        fpu = rig.grid_state.FPU[fpu_id]
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

    save_test_result(dbe, rig.measure_fpuset, keyfunc, valfunc)


def get_datum_result(dbe, fpu_id, dasel=DASEL_BOTH, count=None):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber, RECORD_TYPE, str(dasel))
        return keybase

    return get_test_result(dbe, fpu_id, keyfunc, count=count)


def get_datum_passed_p(dbe, fpu_id, count=None):
    """returns True if the latest datum repeatability test for this FPU
    was passed successfully."""

    val = get_datum_result(dbe, fpu_id, count=count)

    if val is None:
        return False

    return val["result"] == TestResult.OK
