from __future__ import print_function, division

import sys
import time

from os import path
import os
import errno

from numpy import zeros, nan, array

from fpu_commands import gen_wf

from FpuGridDriver import (
    CAN_PROTOCOL_VERSION,
    SEARCH_CLOCKWISE,
    SEARCH_ANTI_CLOCKWISE,
    DEFAULT_WAVEFORM_RULSET_VERSION,
    DATUM_TIMEOUT_DISABLE,
    DASEL_BOTH,
    DASEL_ALPHA,
    DASEL_BETA,
    REQD_ANTI_CLOCKWISE,
    REQD_CLOCKWISE,
    # see documentation reference for Exception hierarchy
    # (for CAN protocol 1, this is section 12.6.1)
    EtherCANException,
    MovementError,
    CollisionError,
    LimitBreachError,
    FirmwareTimeoutError,
    AbortMotionError,
    StepTimingError,
    InvalidStateException,
    SystemFailure,
    InvalidParameterError,
    SetupError,
    InvalidWaveformException,
    ConnectionFailure,
    SocketFailure,
    CommandTimeout,
    ProtectionError,
    HardwareProtectionError,
)

from vfr.conf import (
    DB_TIME_FORMAT,
    IMAGE_ROOT_FOLDER,
    NR360_SERIALNUMBER,
    MTS50_SERIALNUMBER,
)


def flush():
    sys.stdout.flush()


def timestamp():
    return time.strftime(DB_TIME_FORMAT)


def dirac(n, L):
    """return vector of length L with all zeros except a one at position n.
    """
    v = zeros(L, dtype=float)
    v[n] = 1.0
    return v


def goto_position(
    gd,
    abs_alpha,
    abs_beta,
    grid_state,
    fpuset=None,
    allow_uninitialized=False,
    soft_protection=True,
    verbosity=0,
):
    gd.pingFPUs(grid_state)
    current_angles = gd.trackedAngles(grid_state, retrieve=True)
    current_alpha = array([x.as_scalar() for x, y in current_angles])
    current_beta = array([y.as_scalar() for x, y in current_angles])
    if verbosity > 2:
        print ("current positions:\nalpha=%r,\nbeta=%r" % (current_alpha, current_beta))
        print ("moving to (%6.2f,%6.2f)" % (abs_alpha, abs_beta))

    wf = gen_wf(-current_alpha + abs_alpha, -current_beta + abs_beta)
    wf = {k: v for k, v in wf.items() if k in fpuset}
    gd.configMotion(
        wf,
        grid_state,
        allow_uninitialized=allow_uninitialized,
        soft_protection=soft_protection,
        warn_unsafe=soft_protection,
    )

    gd.executeMotion(grid_state, fpuset=fpuset)

    if CAN_PROTOCOL_VERSION == 1:
        gd.pingFPUs(grid_state)


def find_datum(gd, grid_state, opts):

    print ("issuing findDatum:")
    gd.findDatum(grid_state, timeout=DATUM_TIMEOUT_DISABLE)
    print ("findDatum finished")

    # We can use grid_state to display the starting position
    print (
        "the starting position (in degrees) is:",
        gd.trackedAngles(grid_state, retrieve=True),
    )

    return gd, grid_state


def store_image(camera, format_string, **kwargs):

    image_filename = format_string.format(**kwargs)
    ipath = path.join(IMAGE_ROOT_FOLDER, image_filename)

    try:
        os.makedirs(path.dirname(ipath))
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    camera.saveImage(ipath)

    return ipath


def get_sorted_positions(fpuset, positions):
    """we need to sort the turntable angles because 
    we can only move it in rising order"""

    return [(fid, pos) for pos, fid in sorted((positions[fid], fid) for fid in fpuset)]
