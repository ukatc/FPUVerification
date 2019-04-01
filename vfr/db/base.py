from __future__ import absolute_import, division, print_function

import ast
import subprocess

from numpy import array, Inf, NaN, inf, nan # these values are used!!
assert Inf or NaN or inf or nan or array or True

GIT_VERSION = subprocess.check_output(["git", "describe"]).strip()


class TestResult:
    OK = "OK"
    FAILED = "FAILED"
    NA = "NA"


def save_test_result(dbe, fpuset, keyfunc, valfunc, verbosity=None):

    if verbosity is None:
        verbosity = dbe.opts

    with dbe.env.begin(write=True, db=dbe.vfdb) as txn:

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
                print("putting %r : %r" % (key1, count))
                print("putting %r : %r" % (key2, val))

            txn.put(key1, str(count))
            txn.put(key2, val)


def get_test_result(dbe, fpu_id, keyfunc, count=None, verbosity=None):

    if verbosity is None:
        verbosity = dbe.opts.verbosity

    with dbe.env.begin(write=False, db=dbe.vfdb) as txn:

        keybase = keyfunc(fpu_id)

        if (count is None) or (count < 0):
            key1 = str(keybase + ("ntests",))

            try:
                rcount = int(txn.get(key1))
            except TypeError:
                return None

            if count is None:
                # default value: last record
                count = rcount
            else:
                count = rcount - count
                if count < 0:
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
            val["record-count"] = count

        if verbosity > 4:
            print("got %r : %r" % (key2, val))

    return val
