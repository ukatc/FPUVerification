"""

Contains all the utility functions common to all verification tasks.

"""
from __future__ import absolute_import, division, print_function

import errno
import os
import sys
import time
from ast import literal_eval
from math import floor
import numpy as np
import logging
from os import path
from os.path import expanduser, expandvars
from textwrap import dedent
import signal
import warnings
import camera_calibration

# Import functions and constants from the FPU control software (fpu_driver)
from fpu_commands import gen_wf, list_states
from fpu_constants import ALPHA_DATUM_OFFSET, BETA_DATUM_OFFSET
import FpuGridDriver
from FpuGridDriver import (
    CAN_PROTOCOL_VERSION,
)  # see documentation reference for Exception hierarchy; (for CAN protocol 2, this is section ??. \
from FpuGridDriver import (
    DASEL_BOTH,
    DATUM_TIMEOUT_DISABLE,
    DATUM_TIMEOUT_ENABLE,
    FPST_AT_DATUM,
    SEARCH_CLOCKWISE,
    DEFAULT_WAVEFORM_RULESET_VERSION,
)


from vfr.conf import (
    DB_TIME_FORMAT,
    VERIFICATION_ROOT_FOLDER,
    NR360_SERIALNUMBER,
    MTS50_SERIALNUMBER,
)
from ImageAnalysisFuncs.base import ImageAnalysisError

assert tuple(map(int, FpuGridDriver.__version__.split("."))) >= (
    1,
    5,
    5,
), "FPU driver version must be 1.5.5 at least"

got_quit_request = False  # global flag to initiate orderly termination


def handle_quit(signum, stack):
    global got_quit_request
    got_quit_request = True
    logger = logging.getLogger(__name__)
    logger.warning("SIGQUIT received, setting flag to exit")

def request_quit():
    global got_quit_request
    got_quit_request = True
    logger = logging.getLogger(__name__)
    logger.warning("Quit requested, setting flag to exit")

def set_quit_handler():
    signal.signal(signal.SIGQUIT, handle_quit)

def check_for_quit():
    global got_quit_request
    if got_quit_request:
        got_quit_request = False
        raise SystemExit("quit signal received - terminating orderly")

def force_quit():
    raise SystemExit("quit forced - terminating orderly")


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
    """

    Return a vector of length L with all zeros except a one at position n.

    """
    v = np.zeros(L, dtype=float)
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
    loglevel=logging.INFO,
    waveform_ruleset=DEFAULT_WAVEFORM_RULESET_VERSION,
    wf_pars={},
):
    """

    Move FPU(s) to specific absolute alpha and beta angles.

    """
    logger = logging.getLogger(__name__)
    check_for_quit()
    gd.pingFPUs(grid_state)

    # If allow_uninitialized is True, also ensure that movement is enabled
    if allow_uninitialized:
        logger.debug("Enabling movement for %s." % fpuset)
        if fpuset:
            for fpu_id in fpuset:
                gd.enableMove(fpu_id, grid_state)

    current_angles = gd.trackedAngles(grid_state, retrieve=True)
    current_alpha = np.array([x.as_scalar() for x, y in current_angles])
    current_beta = np.array([y.as_scalar() for x, y in current_angles])
    logger.debug("Current positions:\n%r" % current_angles)
    logger.log(
        loglevel, "Moving FPUs %s to (%6.2f,%6.2f)" % (fpuset, abs_alpha, abs_beta)
    )

    delta_alpha = abs_alpha - current_alpha
    delta_beta = abs_beta - current_beta

    # set movement for fpus which are not in set to zero
    for k in range(len(delta_alpha)):
        if fpuset and (k not in fpuset):
            delta_alpha[k] = 0.0
            delta_beta[k] = 0.0

    wf = gen_wf(delta_alpha, delta_beta, **wf_pars)

    gd.configMotion(
        wf,
        grid_state,
        allow_uninitialized=allow_uninitialized,
        soft_protection=soft_protection,
        warn_unsafe=soft_protection,
        verbosity=0,
        ruleset_version=waveform_ruleset,
    )
    check_for_quit()

    gd.executeMotion(grid_state, fpuset=fpuset)
    check_for_quit()

    if CAN_PROTOCOL_VERSION == 1:
        gd.pingFPUs(grid_state)

    logger.trace("FPU states=%s" % str(list_states(grid_state)))


def find_datum(gd, grid_state, opts=None, uninitialized=False, datum_twice=False):
    """

    First move all FPUs to a location close to datum and then find datum.

    """
    logger = logging.getLogger(__name__)
    check_for_quit()
    logger.info("Moving FPUs to datum position")
    gd.pingFPUs(grid_state)

    logger.trace("pre datum: %r" % gd.trackedAngles(grid_state, display=False))
    logger.trace("states= %r" % list_states(grid_state))

    for fpu_id, fpu in enumerate(grid_state.FPU):
        logger.trace(
            "FPU %i (alpha_initalized, beta_initialized) = (%s, %s)"
            % (fpu_id, fpu.alpha_was_referenced, fpu.beta_was_referenced)
        )

    # Check how many FPUs are already at datum.
    unreferenced = []
    for fpu_id, fpu in enumerate(grid_state.FPU):
        if fpu.state != FPST_AT_DATUM:
            unreferenced.append(fpu_id)

    if unreferenced:
        # If not yet referenced, move to a location within 1.0 degrees of datum.
        goto_position(
            gd,
            ALPHA_DATUM_OFFSET + 1.0,
            BETA_DATUM_OFFSET + 1.0,
            grid_state,
            fpuset=unreferenced,
            allow_uninitialized=True,
            soft_protection=True,
        )
        check_for_quit()

        if uninitialized:
            # The first time the FPUs have been datumed
            logger.audit("Issuing initial findDatum (%i FPUs):" % len(unreferenced))

            modes = {fpu_id: SEARCH_CLOCKWISE for fpu_id in unreferenced}

            gd.findDatum(
                grid_state,
                timeout=DATUM_TIMEOUT_DISABLE,
                search_modes=modes,
                selected_arm=DASEL_BOTH,
                fpuset=unreferenced,
            )
            # If required, search for datum a second time to improve accuracy.
            if datum_twice:
                gd.findDatum( grid_state, fpuset=unreferenced )

        else:
            # A second or subsequent findDatum.
            timeout = DATUM_TIMEOUT_ENABLE
            logger.debug(
                "Issuing findDatum (%i FPUs, timeout=%r):"
                % (len(unreferenced), timeout)
            )
            gd.findDatum(grid_state, fpuset=unreferenced, timeout=timeout)
            # Search for datum a second time. The second time is more accurate than the first.
            gd.findDatum( grid_state, fpuset=unreferenced )
            
        logger.trace("findDatum finished, states=%s" % str(list_states(grid_state)))
    else:
        logger.debug("find_datum(): all FPUs already at datum")

    # We can use grid_state to display the starting position
    logger.trace(
        "Datum finished, the FPU positions (in degrees) are: %r"
        % gd.trackedAngles(grid_state, display=False)
    )
    logger.trace("FPU states = %r" % list_states(grid_state))

    check_for_quit()
    return gd, grid_state


def cd_to_data_root(root_folder):
    # Change the working directory to the specified folder.
    logger = logging.getLogger(__name__)
    data_root_path = expanduser(expandvars(root_folder))
    try:
        os.makedirs(data_root_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    logger.debug("changing working directory to %s" % data_root_path)
    os.chdir(data_root_path)


def store_image(camera, format_string, **kwargs):
    """

    Make an exposure with the specified camera and store it to
    a file named in the formatted string.

    """
    # Requires current work directory set to image root folder
    ipath = os.path.join("images", format_string.format(**kwargs))
    print("Images will be saved to:", ipath)

    try:
        os.makedirs(path.dirname(ipath))
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    camera.saveImage(ipath)
    print("Image captured.")

    check_for_quit()
    return ipath


def store_burst_images(camera, nimages, sleep_time_ms, format_string, **kwargs):
    """

    Make a series of exposures with the specified camera and store
    them in files whose names start with the the formatted string.
    Each file name is given a suffix containing the image number.

    """
    # Requires current work directory set to image root folder
    ipath = os.path.join("images", format_string.format(**kwargs))

    try:
        os.makedirs(path.dirname(ipath))
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    camera.saveBurst(ipath, nimages, sleep_time_ms)

    check_for_quit()
    return ipath


def store_one_by_one(camera, nimages, frametime, format_string, **kwargs):
    """

    Make a series of exposures with the specified camera and store
    them in files whose names start with the the formatted string.
    Each file name is given a suffix containing the image number.

    """
    # Requires current work directory set to image root folder
    ipath = os.path.join("images", format_string.format(**kwargs))

    try:
        os.makedirs(path.dirname(ipath))
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

    camera.startGrabbing( nimages, frametime )
    time.sleep( 0.25 )
    camera.triggerGrabbing( frametime, nimages )
    time.sleep( 0.25 )
    camera.finishGrabbing(ipath, nimages, frametime)

    check_for_quit()
    return ipath


def get_sorted_positions(fpuset, positions):
    """

    We need to sort the turntable angles because
    we can only move it in rising order

    """
    return [(fid, pos) for pos, fid in sorted((positions[fid], fid) for fid in fpuset)]


def get_stepcounts(gd, grid_state, fpu_id):
    # Query the FPU grid driver and return alpha and beta step counts
    # for the specified FPU.
    gd.pingFPUs(grid_state)
    alpha_steps = grid_state.FPU[fpu_id].alpha_steps
    beta_steps = grid_state.FPU[fpu_id].beta_steps

    return alpha_steps, beta_steps


def lit_eval_file(file_name):
    # Insert documentation here.
    def not_comment(line):
        lstrip = line.strip()
        if len(lstrip) == 0:
            return False

        return line.strip()[0] != "#"

    return literal_eval("".join(filter(not_comment, open(file_name).readlines())))


def get_config_from_mapfile(filename):
    # Insert documentation here.
    logger = logging.getLogger(__name__)
    map_config = lit_eval_file(filename)
    # current_dir = os.getcwd()
    config_file_name = map_config["calibration_config_file"]
    algorithm = map_config["algorithm"]

    logger.audit(
        "loading cal config from %s/%s" % (VERIFICATION_ROOT_FOLDER, config_file_name)
    )
    config = camera_calibration.Config.load(config_file_name)
    # os.chdir(current_dir)
    config_dict = config.to_dict()

    return {"algorithm": algorithm, "config": config_dict}


def safe_home_turntable(rig, grid_state, opts=None):
    # Home the turntable mechanism.
    check_for_quit()
    logger = logging.getLogger(__name__)
    with rig.lctrl.use_ambientlight():
        find_datum(rig.gd, grid_state, opts=opts)

        st = time.time()
        with rig.hw.pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
            logger.info("Homing stage...")
            # We filter out an annoying warning related to undocumented
            # controller behaviour
            with warnings.catch_warnings():
                warnings.filterwarnings(  #
                    "ignore",
                    "extra message received with"
                    " ID 128, param1=108, param2= 0, data = None",
                    UserWarning,
                    "pyAPT.controller",
                )
                con.home(clockwise=False)
            logger.info("Homing stage... OK")

        logger.debug("\tHoming completed in %.2fs" % (time.time() - st))
    check_for_quit()


def turntable_safe_goto(rig, grid_state, stage_position, wait=True):
    # Move the turntable mechanism to the given stage position.
    check_for_quit()
    logger = logging.getLogger(__name__)
    with rig.lctrl.use_ambientlight():
        find_datum(rig.gd, grid_state, opts=rig.opts)
        logger.info("moving turntable to position %7.3f" % stage_position)
        assert np.isfinite(stage_position), "stage position is not valid number"
        with rig.hw.pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
            logger.trace("Found APT controller S/N %r" % NR360_SERIALNUMBER)
            st = time.time()
            # We filter out an annoying warning related to undocumented
            # controller behaviour
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    "extra message received with"
                    " ID 128, param1=108, param2= 0, data = None",
                    UserWarning,
                    "pyAPT.controller",
                )
                con.goto(stage_position, wait=wait)
            logger.debug("\tMove completed in %.2fs" % (time.time() - st))
            logger.debug("\tNew position: %.3f %s" % (con.position(), con.unit))
            # logger.debug("\tStatus: %r" % con.status())
    check_for_quit()


def home_linear_stage(rig):
    logger = logging.getLogger(__name__)
    check_for_quit()
    with rig.hw.pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        logger.info("\tHoming linear stage...")
        con.home()
        logger.info("\tHoming linear stage... OK")
    check_for_quit()


def linear_stage_goto(rig, stage_position):
    logger = logging.getLogger(__name__)
    check_for_quit()
    logger.info("moving linear stage to position %7.3f ..." % stage_position)
    assert np.isfinite(stage_position), "stage position is not valid number"
    with rig.hw.pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        logger.trace("Found APT controller S/N %s" % str(MTS50_SERIALNUMBER))
        con.goto(stage_position, wait=True)
        logger.debug("\tNew position: %.3f %s" % (con.position(), con.unit))
        logger.trace("\tStatus: %s" % str(con.status()))
    check_for_quit()
    logger.info("moving linear stage to position %f ... OK" % stage_position)


def fixup_ipath(ipath):
    """

    This function fixes up a relocation in relative image database paths, so
    that older test images are still found.  (The reason is that early
    versions stored image pathnames without the "images/" subfolder,
    which required special handling for calibration data.)

    See function store_image above to compare current layout.

    """
    if ipath.startswith("images/"):
        return ipath
    else:
        return os.path.join("images/", ipath)


image_error_count = {}

ECOUNT_QUEUE_LEN = 20  # length of error flag queue for image errors
ECOUNT_LIMIT_WARN = 5  # limit for warnings
ECOUNT_LIMIT_FATAL = 21  # limit to trigger a fatal error


def check_image_analyzability(ipath, analysis_func, pars=None):
    """

    Check whether a captured image can be analyzed successfully,
    and keeps some statistics.
    If this is not the case, it can be a rare failure.
    However if such errors happen frequently,

    """
    fname = analysis_func.__name__
    if not fname in image_error_count:
        image_error_count[fname] = []

    ecount = image_error_count[fname]
    try:
        analysis_func(ipath, pars=pars)
        ecount.append(0)
        if len(ecount) > ECOUNT_QUEUE_LEN:
            ecount.pop(0)

    except ImageAnalysisError as err:
        ecount.append(1)
        if len(ecount) > ECOUNT_QUEUE_LEN:
            ecount.pop(0)
        logger = logging.getLogger(__name__ + "." + fname)
        logger.error(
            "image analysis function %s failed for image %s with message %s"
            % (analysis_func.__name__, ipath, err)
        )
        logger.debug("error statistics for function %s: %r" % (fname, ecount))

        if sum(ecount) >= ECOUNT_LIMIT_WARN:
            logger.warning(
                "image analysis function %s failed at least %i times"
                " for the last %i images- system error possible?"
                % (fname, ECOUNT_LIMIT_WARN, ECOUNT_QUEUE_LEN)
            )
        if sum(ecount) >= ECOUNT_LIMIT_FATAL:
            raise SystemError(
                dedent(
                    """Fatal error:
      Image analysis function %s failed %i times in %i images, failure limit exceeded.
      Last failure was with

      image path name = %r,

      message = %r.

      Stopping verification system."""
                    % (fname, ECOUNT_LIMIT_FATAL, ECOUNT_QUEUE_LEN, ipath, err)
                )
            )
