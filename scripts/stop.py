#!/usr/bin/env python
"""
Usage: python home.py [<serial>]

This program homes all APT controllers found, or of the one specified
"""
from __future__ import absolute_import
from __future__ import print_function

import time
import pyAPT

from runner import runner_serial


@runner_serial
def home(serial):
    #  with pyAPT.MTS50(serial_number=serial) as con:
    #  with pyAPT.NR360S(serial_number=serial) as con:
    with pyAPT.CR1Z7(serial_number=serial) as con:
        con.stop(immediate=True, wait=True)
        print ("stopped")


if __name__ == "__main__":
    import sys

    sys.exit(home())
