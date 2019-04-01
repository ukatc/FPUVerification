from __future__ import absolute_import, division, print_function

from fpu_constants import (
    ALPHA_MAX_DEGREE,
    ALPHA_MIN_DEGREE,
    BETA_DATUM_OFFSET,
    BETA_MAX_DEGREE,
    BETA_MIN_DEGREE,
    DEFAULT_FREE_BETA_RETRIES,
)
from interval import Interval
from protectiondb import ProtectionDB as pdb
from protectiondb import INIT_COUNTERS
from vfr.conf import ALPHA_DATUM_OFFSET
from vfr.tests_common import flush


def init_position(dbe, fpu_id, serialnumber, alpha_start, beta_start):
    sn = serialnumber

    aint = Interval(alpha_start)
    bint = Interval(beta_start)

    waveform_reversed = False

    init_counters = INIT_COUNTERS.copy()

    print(
        "setting FPU #%i, sn=%s to starting position (%r, %r) ... "
        % (fpu_id, serialnumber, alpha_start, beta_start),
        "end=' '",
    )
    flush()

    with dbe.env.begin(write=True, db=dbe.fpudb) as txn:
        if dbe.opts.re_initialize:
            counters = None
        else:
            counters = pdb.getRawField(txn, sn, pdb.counters)

        if counters != None:
            init_counters.update(counters)

        pdb.putInterval(txn, sn, pdb.alpha_positions, aint, ALPHA_DATUM_OFFSET)
        pdb.putInterval(txn, sn, pdb.beta_positions, bint, BETA_DATUM_OFFSET)
        pdb.putField(txn, sn, pdb.waveform_table, [])
        pdb.putField(txn, sn, pdb.waveform_reversed, waveform_reversed)
        pdb.putInterval(
            txn,
            sn,
            pdb.alpha_limits,
            Interval(ALPHA_MIN_DEGREE, ALPHA_MAX_DEGREE),
            ALPHA_DATUM_OFFSET,
        )
        pdb.putInterval(
            txn,
            sn,
            pdb.beta_limits,
            Interval(BETA_MIN_DEGREE, BETA_MAX_DEGREE),
            BETA_DATUM_OFFSET,
        )
        pdb.putField(txn, sn, pdb.free_beta_retries, DEFAULT_FREE_BETA_RETRIES)
        pdb.putField(txn, sn, pdb.beta_retry_count_cw, 0)
        pdb.putField(txn, sn, pdb.beta_retry_count_acw, 0)
        pdb.putField(txn, sn, pdb.counters, init_counters)

    print("OK")
