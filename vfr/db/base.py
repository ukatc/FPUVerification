from __future__ import absolute_import, division, print_function

import ast
import inspect
import logging
import os.path
import subprocess

from argparse import Namespace

# "Namespace" is needed in eval()
assert Namespace
from numpy import array, Inf, NaN, inf, nan  # these values are used!!

assert Inf or NaN or inf or nan or array or True

from vfr.tests_common import timestamp


def get_version():
    start_dir = os.getcwd()
    source_dir = os.path.dirname(inspect.getsourcefile(get_version))
    os.chdir(source_dir)
    version = subprocess.check_output(["git", "describe"]).strip()
    os.chdir(start_dir)

    return version


GIT_VERSION = get_version()


class TestResult:
    OK = "OK"
    FAILED = "FAILED"
    NA = "NA"


def save_test_result(dbe, fpuset, keyfunc, valfunc):
    trace = logging.getLogger(__name__).trace

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

            trace("putting %r : %r" % (key1, count))
            trace("putting %r : %r" % (key2, val))

            txn.put(key1, str(count))
            txn.put(key2, val)


def get_test_result(dbe, fpu_id, keyfunc, count=None):

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
                # Resolve Namespace constructors.
                # We also need to work around the disappointing fact that
                # literal_eval() does not recognize IEEE754 NaN
                # symbols.
                val = eval(val)
            val["record-count"] = count

        trace = logging.getLogger(__name__).trace
        trace("got %r : %r" % (key2, val))

    return val


def save_named_record(
    record_type, dbe, fpu_id, record, include_fpu_id=False, loglevel=logging.DEBUG - 5
):

    log = logging.getLogger(__name__).trace

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber,) + record_type
        return keybase

    def valfunc(fpu_id):

        val = dict(**vars(record))
        val.update({"git_version": GIT_VERSION, "time": timestamp()})
        if include_fpu_id:
            val.update({"fpu_id": fpu_id})
        return repr(val)

    log(loglevel, "saving {!r} = {!r}".format(record_type, record))

    save_test_result(dbe, [fpu_id], keyfunc, valfunc)


def get_named_record(record_type, dbe, fpu_id, count=None, loglevel=logging.DEBUG - 5):

    # define two closures - one for the unique key, another for the stored value
    def keyfunc(fpu_id):
        serialnumber = dbe.fpu_config[fpu_id]["serialnumber"]
        keybase = (serialnumber,) + record_type
        return keybase

    rval = get_test_result(dbe, fpu_id, keyfunc, count=count)

    logger = logging.getLogger(__name__)
    logger.log(loglevel, "getting " + str(record_type))

    return rval
