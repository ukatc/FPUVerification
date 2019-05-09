from __future__ import absolute_import, division, print_function

import errno
import os
import sys
import time
from ast import literal_eval
from math import floor
from numpy import isfinite
import logging
from os import path
from os.path import expanduser, expandvars
import signal
import warnings
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
    VERIFICATION_ROOT_FOLDER,
    NR360_SERIALNUMBER,
    MTS50_SERIALNUMBER,
)
from ImageAnalysisFuncs.base import ImageAnalysisError


got_quit_request = False # global flag to initiate orderly termination

def handle_quit(signum, stack):
    global got_quit_request
    got_quit_request = True
    logger = logging.getLogger(__name__)
    logger.warning("SIGQUIT received, setting flag to exit")

def set_quit_handler():
    signal.signal(signal.SIGQUIT, handle_quit)

def check_for_quit():
    global got_quit_request
    if got_quit_request:
        got_quit_request = False
        raise SystemExit("quit signal received - terminating orderly")


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
    loglevel=logging.INFO,
):
    logger = logging.getLogger(__name__)
    check_for_quit()
    gd.pingFPUs(grid_state)
    current_angles = gd.trackedAngles(grid_state, retrieve=True)
    current_alpha = array([x.as_scalar() for x, y in current_angles])
    current_beta = array([y.as_scalar() for x, y in current_angles])
    logger.debug("current positions:\n%r" % current_angles)
    logger.log(loglevel, "moving FPUs %s to (%6.2f,%6.2f)" % (fpuset, abs_alpha, abs_beta))

    wf = gen_wf(abs_alpha - current_alpha, abs_beta - current_beta)
    wf2 = {k: v for k, v in wf.items() if k in fpuset}
    gd.configMotion(
        wf2,
        grid_state,
        allow_uninitialized=allow_uninitialized,
        soft_protection=soft_protection,
        warn_unsafe=soft_protection,
        verbosity=0,
    )
    check_for_quit()

    gd.executeMotion(grid_state, fpuset=fpuset)
    check_for_quit()

    if CAN_PROTOCOL_VERSION == 1:
        gd.pingFPUs(grid_state)

    logger.trace("FPU states=", list_states(grid_state))


def find_datum(gd, grid_state, opts=None, uninitialized=False):

    logger = logging.getLogger(__name__)
    check_for_quit()
    logger.info("moving FPUs to datum position")
    gd.pingFPUs(grid_state)

    logger.trace("pre datum: %r" % gd.trackedAngles(grid_state, display=False) )
    logger.trace("states= %r" % list_states(grid_state))

    for fpu_id, fpu in enumerate(grid_state.FPU):
      logger.trace(
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
        )
        check_for_quit()

        if uninitialized:
            logger.audit("issuing initial findDatum (%i FPUs):" % len(unreferenced))

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
            logger.debug(
                    "issuing findDatum (%i FPUs, timeout=%r):"
                    % (len(unreferenced), timeout)
                )
            gd.findDatum(grid_state, fpuset=unreferenced, timeout=timeout)

        logger.trace("findDatum finished, states=", list_states(grid_state))
    else:
      logger.debug("find_datum(): all FPUs already at datum")

    # We can use grid_state to display the starting position
    logger.trace(
      "datum finished, the FPU positions (in degrees) are: %r" %
      gd.trackedAngles(grid_state, display=False),
    )
    logger.trace("FPU states = %r" % list_states(grid_state))

    check_for_quit()
    return gd, grid_state


def cd_to_data_root(root_folder):
    logger = logging.getLogger(__name__)
    data_root_path = expanduser(expandvars(root_folder))
    try:
        os.makedirs(data_root_path)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    logger.debug("changing working directory to %s" % data_root_path)
    os.chdir(data_root_path)


def store_image(camera, format_string, **kwargs):
    logger = logging.getLogger(__name__)

    # requires current work directory set to image root folder
    ipath = os.path.join("images", format_string.format(**kwargs))

    try:
        os.makedirs(path.dirname(ipath))
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    camera.saveImage(ipath)

    check_for_quit()
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
    logger = logging.getLogger(__name__)
    map_config = lit_eval_file(filename)
    # current_dir = os.getcwd()
    config_file_name = map_config["calibration_config_file"]
    algorithm = map_config["algorithm"]

    logger.audit("loading cal config from %s/%s" % (VERIFICATION_ROOT_FOLDER, config_file_name))
    config = camera_calibration.Config.load(config_file_name)
    # os.chdir(current_dir)
    config_dict = config.to_dict()

    return {"algorithm": algorithm, "config": config_dict}


def safe_home_turntable(rig, grid_state, opts=None):
    check_for_quit()
    logger = logging.getLogger(__name__)
    with rig.lctrl.use_ambientlight():
        find_datum(rig.gd, grid_state, opts=opts)

        st = time.time()
        with rig.hw.pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
            logger.info("Homing stage...")
            # we filter out an annoying warning related to undocumented
            # controller behaviour
            with warnings.catch_warnings():
              warnings.filterwarnings(#
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
    check_for_quit()
    logger = logging.getLogger(__name__)
    with rig.lctrl.use_ambientlight():
        find_datum(rig.gd, grid_state, opts=rig.opts)
        logger.info("moving turntable to position %7.3f" % stage_position)
        assert isfinite(stage_position), "stage position is not valid number"
        with rig.hw.pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
            logger.trace("Found APT controller S/N %r" % NR360_SERIALNUMBER)
            st = time.time()
            # we filter out an annoying warning related to undocumented
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
            #logger.debug("\tStatus: %r" % con.status())
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
    assert isfinite(stage_position), "stage position is not valid number"
    with rig.hw.pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        logger.trace("Found APT controller S/N", MTS50_SERIALNUMBER)
        con.goto(stage_position, wait=True)
        logger.debug("\tNew position: %.3f %s" % (con.position(), con.unit))
        logger.trace("\tStatus:", con.status())
    check_for_quit()
    logger.info("moving linear stage to position %f ... OK" % stage_position)


def fixup_ipath(ipath):
  """this fixes up a relocation in relative image database paths, so
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

ECOUNT_QUEUE_LEN = 20 # length of error flag queue for image errors
ECOUNT_LIMIT_WARN = 5 # limit for warnings
ECOUNT_LIMIT_FATAL = 3 # limit to trigger a fatal error

def check_image_analyzability(ipath, analysis_func, pars=None):
  """Check whether a captured image can be analyzed successfully,
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

  except ImageAnalysisError, err:
    ecount.append(1)
    if len(ecount) > ECOUNT_QUEUE_LEN:
      ecount.pop(0)
    logger = logging.getLogger(__name__ + '.' + fname)
    logger.error("image analysis function %s failed for image %s with message %s" % (
      analysis_func.__name__,
      ipath,
      err))
    logger.debug("error statistics for function %s: %r" % (fname, ecount))

    if sum(ecount) >= ECOUNT_LIMIT_WARN:
      logger.warning("image analysis function %s failed at least %i times"
                     " for the last %i images- system error possible?" % (
                       fname, ECOUNT_LIMIT_WARN, ECOUNT_QUEUE_LEN))
    if sum(ecount) >= ECOUNT_LIMIT_FATAL:
      raise SystemError("image analysis function %s failed %i times in %i images,"
                        " last with image %s, message %s. Stopping verification system." % (
                          fname, ECOUNT_LIMIT_FATAL, ECOUNT_QUEUE_LEN, ipath, err))
