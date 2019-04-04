from __future__ import absolute_import, division, print_function

import sys
import time

from numpy import isfinite

import pyAPT
from GigE.GigECamera import GigECamera
from Lamps.lctrl import lampController, manualLampController
from vfr.tests_common import find_datum
from vfr.conf import NR360_SERIALNUMBER, MTS50_SERIALNUMBER

"""this module simply bundles all real hardware access functions
so that they can be easily swapped out by mock-up functions."""

# these assertions are there to make pyflakes happy
assert GigECamera
assert lampController
assert manualLampController


def safe_home_turntable(gd, grid_state, opts=None):
    find_datum(gd, grid_state, opts=opts)

    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        print("\tHoming stage...", "end=' '")
        con.home(clockwise=False)
        print("homed")
    print("OK")


def turntable_safe_goto(gd, grid_state, stage_position, wait=True, monitor=False):
    gd.findDatum(grid_state)
    print("moving turntable to position %f" % stage_position)
    assert isfinite(stage_position), "stage position is not valid number"
    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        print("Found APT controller S/N", NR360_SERIALNUMBER)
        st = time.time()
        con.goto(stage_position, wait=wait)
        #        if monitor:
        #            stat = con.status()
        #            while stat.moving:
        #                out = "        pos %3.2f %s vel %3.2f %s/s" % (
        #                    stat.position,
        #                    con.unit,
        #                    stat.velocity,
        #                    con.unit,
        #                )
        #                sys.stdout.write(out)
        #                time.sleep(0.01)
        #                stat = con.status()
        #                l = len(out)
        #                sys.stdout.write("\b" * l)
        #                sys.stdout.write(" " * l)
        #                sys.stdout.write("\b" * l)
        print("\tMove completed in %.2fs" % (time.time() - st))
        print("\tNew position: %.2f %s" % (con.position(), con.unit))
        if monitor:
            print("\tStatus:", con.status())
        return 0

        print("\tNew position: %.2fmm %s" % (con.position(), con.unit))
        print("\tStatus:", con.status())
    print("OK")


def home_linear_stage():
    with pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        print("\tHoming linear stage...", "end=' '")
        con.home()
        print("homed")
    print("OK")


def linear_stage_goto(stage_position):
    print("moving linear stage to position %f" % stage_position)
    assert isfinite(stage_position), "stage position is not valid number"
    with pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        print("Found APT controller S/N", MTS50_SERIALNUMBER)
        con.goto(stage_position, wait=True)
        print("\tNew position: %.2fmm %s" % (con.position(), con.unit))
        print("\tStatus:", con.status())
    print("OK")
