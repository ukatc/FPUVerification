from __future__ import print_function, division

import sys
import time

from vfr.conf import DB_TIME_FORMAT

def flush():
    sys.stdout.flush()


def timestamp():
    return time.strftime(DB_TIME_FORMAT)
