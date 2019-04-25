from __future__ import absolute_import, division, print_function

import errno
import os
import sys
import time
from ast import literal_eval
from math import floor
from numpy import isfinite

from os import path
from os.path import expanduser, expandvars
import camera_calibration

from fpu_commands import gen_wf, list_states
from fpu_constants import ALPHA_DATUM_OFFSET, BETA_DATUM_OFFSET
from FpuGridDriver import (
    CAN_PROTOCOL_VERSION,
)  # see documentation reference for Exception hierarchy; (for CAN protocol 1, this is section 12. \
from FpuGridDriver import (
    DASEL_BOTH,
    DATUM_TIMEOUT_DISABLE,
    DATUM_TIMEOUT_ENABLE,
    FPST_AT_DATUM,
    SEARCH_CLOCKWISE,
)
from numpy import array, zeros
from vfr.conf import (
    DB_TIME_FORMAT,
    IMAGE_ROOT_FOLDER,
    NR360_SERIALNUMBER,
    MTS50_SERIALNUMBER,
)


def flush():
    sys.stdout.flush()


def timestamp():
    ti = time.strftime(DB_TIME_FORMAT)
    # get milliseconds
    fs = time.time()
    ms = "%03i" % int((fs - floor(fs)) * 1000)
    # replace
    return ti.replace("~", ms)


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
    if verbosity > 8:
        print("current positions:\n%r" % current_angles)
    if verbosity > 0:
        print("moving FPUs %s to (%6.2f,%6.2f)" % (fpuset, abs_alpha, abs_beta))

    wf = gen_wf(abs_alpha - current_alpha, abs_beta - current_beta)
    wf2 = {k: v for k, v in wf.items() if k in fpuset}
    verbosity = max(verbosity - 3, 0)
    gd.configMotion(
        wf2,
        grid_state,
        allow_uninitialized=allow_uninitialized,
        soft_protection=soft_protection,
        warn_unsafe=soft_protection,
        verbosity=verbosity,
    )

    gd.executeMotion(grid_state, fpuset=fpuset)

    if CAN_PROTOCOL_VERSION == 1:
        gd.pingFPUs(grid_state)

    if verbosity > 8:
        print("FPU states=", list_states(grid_state))


def find_datum(gd, grid_state, opts=None, uninitialized=False):

    verbosity = opts.verbosity if opts else 0
    gd.pingFPUs(grid_state)
    if verbosity > 9:
        print("pre datum:")
        gd.trackedAngles(grid_state)
    if verbosity > 9:
        print("states=", list_states(grid_state))
    if verbosity > 8:
        for fpu_id, fpu in enumerate(grid_state.FPU):
            print(
                "FPU %i (alpha_initalized, beta_initialized) = (%s, %s)"
                % (fpu_id, fpu.alpha_was_zeroed, fpu.beta_was_zeroed)
            )

    unreferenced = []
    for fpu_id, fpu in enumerate(grid_state.FPU):
        if fpu.state != FPST_AT_DATUM:
            unreferenced.append(fpu_id)

    if unreferenced:
        goto_position(
            gd,
            ALPHA_DATUM_OFFSET + 1.0,
            BETA_DATUM_OFFSET + 1.0,
            grid_state,
            fpuset=unreferenced,
            allow_uninitialized=True,
            soft_protection=True,
            verbosity=verbosity,
        )

        if uninitialized:
            if verbosity > 0:
                print("issuing initial findDatum (%i FPUs):" % len(unreferenced))

            modes = {fpu_id: SEARCH_CLOCKWISE for fpu_id in unreferenced}

            gd.findDatum(
                grid_state,
                timeout=DATUM_TIMEOUT_DISABLE,
                search_modes=modes,
                selected_arm=DASEL_BOTH,
                fpuset=unreferenced,
            )

        else:
            timeout = DATUM_TIMEOUT_ENABLE
            if verbosity > 3:
                print(
                    "issuing findDatum (%i FPUs, timeout=%r):"
                    % (len(unreferenced), timeout)
                )
            gd.findDatum(grid_state, fpuset=unreferenced, timeout=timeout)

        if verbosity > 5:
            print("findDatum finished, states=", list_states(grid_state))
    else:
        if verbosity > 1:
            print("find_datum(): all FPUs already at datum")

    # We can use grid_state to display the starting position
    if verbosity > 9:
        print(
            "datum finished, the FPU positions (in degrees) are:",
            gd.trackedAngles(grid_state, retrieve=True),
        )
    if verbosity > 9:
        print("FPU states = ", list_states(grid_state))

    return gd, grid_state


def cd_to_image_root(image_root_folder):
    image_root_path = expanduser(expandvars(image_root_folder))
    try:
        os.makedirs(image_root_path)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    os.chdir(image_root_path)


def store_image(camera, format_string, **kwargs):

    # requires current work directory set to image root folder
    ipath = format_string.format(**kwargs)

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


def get_stepcounts(gd, grid_state, fpu_id):
    gd.pingFPUs(grid_state)
    alpha_steps = grid_state.FPU[fpu_id].alpha_steps
    beta_steps = grid_state.FPU[fpu_id].beta_steps

    return alpha_steps, beta_steps


def lit_eval_file(file_name):
    def not_comment(line):
        if len(line) == 0:
            return False

        return line.strip()[0] != "#"

    return literal_eval("".join(filter(not_comment, open(file_name).readlines())))


def get_config_from_mapfile(filename):
    map_config = lit_eval_file(path.join("..", filename))
    # current_dir = os.getcwd()
    # cd_to_image_root(path.join(IMAGE_ROOT_FOLDER, ".."))
    config_file_name = map_config["calibration_config_file"]
    algorithm = map_config["algorithm"]

    rel_config_file_name = path.join("..", config_file_name)
    print("loading cal config from %s/%s" % (IMAGE_ROOT_FOLDER, rel_config_file_name))
    config = camera_calibration.Config.load(rel_config_file_name)
    # os.chdir(current_dir)
    config_dict = config.to_dict()

    return {"algorithm": algorithm, "config": config_dict}


def safe_home_turntable(rig, grid_state, opts=None):
    with rig.lctrl.use_ambientlight():
        find_datum(rig.gd, grid_state, opts=opts)

        with rig.hw.pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
            print("\tHoming stage...", end=" ")
            con.home(clockwise=False)
            print("homed")
        print("OK")


def turntable_safe_goto(rig, grid_state, stage_position, wait=True, monitor=False):
    with rig.lctrl.use_ambientlight():
        find_datum(rig.gd, grid_state, opts=rig.opts)
        print("moving turntable to position %f" % stage_position)
        assert isfinite(stage_position), "stage position is not valid number"
        with rig.hw.pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
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

            print("\tNew position: %.2f %s" % (con.position(), con.unit))
            print("\tStatus:", con.status())
    print("OK")


def home_linear_stage(rig):
    with rig.hw.pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        print("\tHoming linear stage...", end=" ")
        con.home()
        print("homed")
    print("OK")


def linear_stage_goto(rig, stage_position):
    print("moving linear stage to position %f" % stage_position)
    assert isfinite(stage_position), "stage position is not valid number"
    with rig.hw.pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        print("Found APT controller S/N", MTS50_SERIALNUMBER)
        con.goto(stage_position, wait=True)
        print("\tNew position: %.2f %s" % (con.position(), con.unit))
        print("\tStatus:", con.status())
    print("OK")
