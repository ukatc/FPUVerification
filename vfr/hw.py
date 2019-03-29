from __future__ import absolute_import, division, print_function

import pyAPT
from GigE.GigECamera import GigECamera
from Lamps.lctrl import lampController
from vfr.tests_common import find_datum
from vfr.conf import NR360_SERIALNUMBER, MTS50_SERIALNUMBER

"""this module simply bundles all real hardware access functions
so that they can be easily swapped out by mock-up functions."""

assert GigECamera
assert lampController

def safe_home_turntable(gd, grid_state, opts=None):
    find_datum(gd, grid_state, opts=opts)

    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        print("\tHoming stage...", "end=' '")
        con.home(clockwise=True)
        print("homed")


def turntable_safe_goto(gd, grid_state, stage_position):
    gd.findDatum(grid_state)
    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        print("Found APT controller S/N", NR360_SERIALNUMBER)
        con.goto(stage_position, wait=True)
        print("\tNew position: %.2fmm %s" % (con.position(), con.unit))
        print("\tStatus:", con.status())


def home_linear_stage():
    with pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        print("\tHoming linear stage...", "end=' '")
        con.home(clockwise=True)
        print("homed")


def linear_stage_goto(stage_position):
    with pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        print("Found APT controller S/N", MTS50_SERIALNUMBER)
        con.goto(stage_position, wait=True)
        print("\tNew position: %.2fmm %s" % (con.position(), con.unit))
        print("\tStatus:", con.status())
