#!/usr/bin/env python
"""
Usage: python move.py <serial> <distance_mm>

This program tells the specified controller to move the stage by the specified
distance in mm
"""
from __future__ import absolute_import, print_function

import pyAPT
import pylibftdi


def main(args):
    if len(args) < 3:
        print(__doc__)
        return 1
    else:
        serial = args[1]
        dist = float(args[2])

    try:
        with pyAPT.NR360S(serial_number=serial) as con:
            print("Found APT controller S/N", serial)
            print("\tMoving stage by %.2fmm..." % (dist), end=" ")
            con.move(dist)
            print("moved")
            print("\tNew position: %.2f %s" % (con.position(), con.unit))
            return 0
    except pylibftdi.FtdiError:
        print("\tCould not find APT controller S/N of", serial)
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
