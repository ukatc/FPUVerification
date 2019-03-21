from __future__ import print_function, division

import os
import ast
import lmdb
import platform
import subprocess

from vfr.tests_common import timestamp
from numpy import NaN, nan

GIT_VERSION = subprocess.check_output(["git", "describe"]).strip()


class TestResult:
    OK = "OK"
    FAILED = "FAILED"
    NA = "NA"


def save_test_result(ctx, fpuset, keyfunc, valfunc):

    verbosity = ctx.opts

    with ctx.env.begin(write=True, db=ctx.vfdb) as txn:

        for fpu_id in fpuset:

            keybase = keyfunc(fpu_id)
            key1 = str(keybase + ("ntests",))

            last_cnt = txn.get(key1)
            if last_cnt is None:
                count = 0
            else:
                count = int(last_cnt) + 1

            key2 = repr(keybase + ("data", count))

            val = valfunc(fpu_id)

            if verbosity > 4:
                print ("putting %r : %r" % (key1, count))
                print ("putting %r : %r" % (key2, val))

            txn.put(key1, str(count))
            txn.put(key2, val)


def get_test_result(ctx, fpu_id, keyfunc, count=None):

    verbosity = ctx.opts.verbosity

    with ctx.env.begin(write=False, db=ctx.vfdb) as txn:

        keybase = keyfunc(fpu_id)

        if count is None:
            key1 = str(keybase + ("ntests",))

            try:
                count = int(txn.get(key1))
            except TypeError:
                return None

        key2 = repr(keybase + ("data", count))

        val = txn.get(key2)

        if val is not None:
            try:
                val = ast.literal_eval(val)

            except ValueError:
                # we need to work around the disappointing fact that
                # literal_eval() does not recognize IEEE754 NaN
                # symbols
                val = eval(val)

        if verbosity > 4:
            print ("got %r : %r" % (key2, val))

    return val
