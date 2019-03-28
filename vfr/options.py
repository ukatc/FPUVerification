from __future__ import absolute_import, division, print_function

import argparse
import re
import sys
import types
import warnings
from ast import literal_eval
from os import environ

from fpu_constants import ALPHA_MIN_DEGREE, ALPHA_MAX_DEGREE, BETA_MIN_DEGREE, BETA_MAX_DEGREE
from vfr.conf import DEFAULT_TASKS
from vfr.db.snset import get_snset
from vfr.helptext import examples, summary
from vfr.TaskLogic import T
from vfr.task_config import usertasks


def parse_args():
    try:
        DEFAULT_VERBOSITY = int(environ.get("VFR_VERBOSITY", "1"))
    except:
        print("VFR_VERBOSITY has invalid value, setting verbosity to one")
        DEFAULT_VERBOSITY = 1

    parser = argparse.ArgumentParser(
        description=summary.format(DEFAULT_TASKS=DEFAULT_TASKS, **T.__dict__),
        epilog=examples.format(DEFAULT_TASKS=DEFAULT_TASKS, **T.__dict__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "tasks",
        nargs="*",
        default=DEFAULT_TASKS,
        help="""list of tasks to perform (default: %(default)s)""",
    )

    parser.add_argument(
        "-f",
        "--setup-file",
        default="fpus_batch0.cfg",
        type=str,
        help="set FPU flashing and measurement configuration file",
    )

    parser.add_argument(
        "-l",
        "--list-tasks",
        default=False,
        action="store_true",
        help="list all task names which can be selected directly",
    )

    parser.add_argument(
        "-fmt",
        "--report-format",
        default="terse",
        choices=["status", "brief", "terse", "short", "long", "extended"],
        help="""output format of 'report' task (one of 'status', 'terse', 'short', 'long',
        'extended', default is 'terse'). The options do the following:

        'status': print one line with the overall status for each FPU
        'brief' : print one line for each test section
        'terse' : print essential information
        'short' : print additional information, like angles with maximum errors
        'long'  : in addition, list values for each angle
        'extended' : print nearly full information, including a list of images"""
    )

    parser.add_argument(
        "-m",
        "--mockup",
        default=False,
        action="store_true",
        help="set gateway address to use mock-up gateway and FPU",
    )

    parser.add_argument(
        "-mlc",
        "--manual-lamp-control",
        default=False,
        action="store_true",
        help="switch to manual lamp control",
    )

    parser.add_argument(
        "-reset",
        "--resetFPUs",
        default=False,
        action="store_true",
        help="reset all FPUs so that earlier aborts / collisions are ignored",
    )

    parser.add_argument(
        "-ar",
        "--alwaysResetFPUs",
        default=False,
        action="store_true",
        help="reset FPUs between each step of functional tests so that previous aborts / collisions are ignored",
    )

    parser.add_argument(
        "-ri",
        "--re-initialize",
        default=False,
        action="store_true",
        help="re-initialize FPU counters even if entry exists",
    )

    parser.add_argument(
        "-sn",
        "--snset",
        default=None,
        help="""apply tasks only to passed set of serial numbers, passed as "['MP001', 'MP002', ...]",
        or just as single serial number, as 'MP001' """,
    )

    parser.add_argument(
        "-o",
        "--output-file",
        default=None,
        type=str,
        help="output file for report and dump (defaults to stdout)",
    )

    parser.add_argument(
        "-rsn",
        "--reuse-serialnum",
        default=False,
        action="store_true",
        help="reuse serial number",
    )

    parser.add_argument(
        "-rpt",
        "--repeat-passed-tests",
        default=False,
        action="store_true",
        help="repeat tests which were already passed successfully",
    )

    parser.add_argument(
        "-upl",
        "--update-protection-limits",
        default=False,
        action="store_true",
        help="update range limits to protection database, even if it was already set",
    )

    parser.add_argument(
        "-ptl",
        "--protection-tolerance",
        type=float,
        default=0.2,
        help="tolerance used when deriving protection limits from empirical range (default: %(default)s).",
    )

    parser.add_argument(
        "-i",
        "--reinit-db",
        default=False,
        action="store_true",
        help="reinitialize posiiton database entry",
    )

    parser.add_argument(
        "-sf",
        "--skip-fibre",
        default=False,
        action="store_true",
        help="skip measurements and dependencies which require fibres to be present",
    )

    parser.add_argument(
        "-rw",
        "--rewind_fpus",
        default=False,
        action="store_true",
        help="rewind FPUs to datum position at start",
    )

    parser.add_argument(
        "-gp",
        "--gateway_port",
        metavar="GATEWAY_PORT",
        type=int,
        default=4700,
        help="EtherCAN gateway port number (default: %(default)s)",
    )

    parser.add_argument(
        "-ga",
        "--gateway_address",
        metavar="GATEWAY_ADDRESS",
        type=str,
        default="192.168.0.10",
        help="EtherCAN gateway IP address or hostname (default: %(default)r)",
    )

    parser.add_argument(
        "-N",
        "--NUM_FPUS",
        metavar="NUM_FPUS",
        dest="N",
        type=int,
        default=6,
        help="Number of adressed FPUs (default: %(default)s).",
    )

    parser.add_argument(
        "-dd",
        "--bus-repeat-dummy-delay",
        metavar="BUS_REPEAT_DUMMY_DELAY",
        type=int,
        default=2,
        help="Dummy delay inserted before writing to the same bus (default: %(default)s).",
    )

    parser.add_argument(
        "--display-alpha-min",
        metavar="DISPLAY_ALPHA_MIN",
        type=float,
        default=ALPHA_MIN_DEGREE,
        help="minimum alpha value displayed in 'long' report format  (default: %(default)s)",
    )

    parser.add_argument(
        "--display-alpha-max",
        metavar="DISPLAY_ALPHA_MAX",
        type=float,
        default=ALPHA_MAX_DEGREE,
        help="maximum alpha value displayed in 'long' report format  (default: %(default)s)",
    )

    parser.add_argument(
        "--display-beta-min",
        metavar="DISPLAY_BETA_MIN",
        type=float,
        default=BETA_MIN_DEGREE,
        help="minimum beta value displayed in 'long' report format  (default: %(default)s)",
    )

    parser.add_argument(
        "--display-beta-max",
        metavar="DISPLAY_BETA_MAX",
        type=float,
        default=BETA_MAX_DEGREE,
        help="maximum beta value displayed in 'long' report format  (default: %(default)s)",
    )

    parser.add_argument(
        "-cnt",
        "--record-count",
        metavar="RECORD_COUNT",
        type=int,
        default=None,
        help="record number to be retrieved in report, negative values count"
        " back from the latest. Default is the latest record.",
    )

    parser.add_argument(
        "-v",
        "--verbosity",
        metavar="VERBOSITY",
        type=int,
        default=DEFAULT_VERBOSITY,
        help="verbosity level of progress messages, between 0 and 15 "
        "(can be set by environment variable VFR_VERBOSITY, default: %(default)s)",
    )

    args = parser.parse_args()

    if args.list_tasks:
        print("available tasks in alphabetic order: %r" % sorted(list(usertasks)))
        sys.exit(0)

    if len(args.tasks) == 0:
        args.tasks = DEFAULT_TASKS

    if args.mockup:
        args.gateway_address = "127.0.0.1"
        args.gateway_port = 4700

    if args.output_file is None:
        args.output_file = sys.stdout
    else:
        args.output_file = open(args.output_file, "w")

    return args


sn_pat = re.compile("[a-zA-Z0-9]{1,5}$")


def get_sets(env, vfdb, fpu_config, opts):
    """Under normal operation, we want to measure and evaluate the FPUs
    in the rig.

    However, we also need to be able to query and/or re-evaluate data
    for FPUs which have been measured before. To do that, there is a
    command line parameter so that we can select a subset of all
    stored FPUs to be displayed.

    This allows also to restrict a new measurement to FPUs which are
    explicityly listed, for example because the need to be selectively
    repeated.

    """
    eval_snset = opts.snset

    if eval_snset == "all":
        # get the serial numbers of all FPUs which have been measured so far
        eval_snset = get_snset(env, vfdb, opts)
        # this is a workaround against dirty data
        eval_snset = set(filter(lambda x: type(x) == types.StringType, eval_snset))
        fpu_config = {}
    else:
        if eval_snset is not None:
            # in this case, it needs to be a literal list of serial numbers,
            # a string with a quoted string literal, or a string
            try:
                val = literal_eval(eval_snset)
            except ValueError:
                val = eval_snset

            if type(val) == types.ListType:
                eval_snset = set(val)
            else:
                eval_snset = set([val])

            # check passed serial numbers for validity
            for sn in eval_snset:
                if not sn_pat.match(sn):
                    raise ValueError("serial number %r is not valid!" % sn)

    if eval_snset is None:
        # both mesured and evaluated sets are exclusively defined by
        # the measurement configuration file
        measure_fpuset = fpu_config.keys()
        eval_fpuset = measure_fpuset
    else:
        for sn in eval_snset:
            if not sn_pat.match(sn):
                raise ValueError("serial number %r is not valid!" % sn)

        # we restrict the measured FPUs to the serial numbers passed
        # in the command line option, and create a config which has
        # entries for these and the additional requested serial
        # numbers
        config_by_sn = {val["serialnumber"]: val for val in fpu_config.values()}

        config_sns = set(config_by_sn.keys())
        if len(config_sns) != len(fpu_config):
            raise ValueError(
                "the measurement configuration file has duplicate serial numbers"
            )

        measure_sns = config_sns.intersection(eval_snset)

        measure_config = {
            config_by_sn[sn]["fpu_id"]: config_by_sn[sn] for sn in measure_sns
        }

        measure_fpuset = set(measure_config.keys())

        extra_eval_sns = eval_snset.difference(measure_sns)

        # we use the serial numbers as key - these need not to have
        # integer type as they are not used in measurements.

        fpu_config = {sn: {"serialnumber": sn} for sn in extra_eval_sns}

        fpu_config.update(measure_config)

        eval_fpuset = fpu_config.keys()

        # get sets of measured and evaluated FPUs
        if measure_fpuset:
            N = max(measure_fpuset) + 1
        else:
            N = 0

        if N < opts.N:
            warnings.warn("Subset selected. Adjusting number of addressed FPUs to %i." % N)
            opts.N = N

    return fpu_config, sorted(measure_fpuset), sorted(eval_fpuset)


def load_config(env, vfdb, config_file_name, opts=None):
    print("reading measurement configuratiom from %r..." % config_file_name)
    cfg_list = literal_eval("".join(open(config_file_name).readlines()))

    fconfig = dict(
        [
            (
                entry["fpu_id"],
                {
                    "serialnumber": entry["serialnumber"],
                    "pos": entry["pos"],
                    "fpu_id": entry["fpu_id"],
                },
            )
            for entry in cfg_list
        ]
    )

    for key, val in fconfig.items():
        if key < 0:
            raise ValueError("FPU id %i is not valid!" % key)
        serialnumber = val["serialnumber"]
        if not sn_pat.match(serialnumber):
            raise ValueError(
                "serial number %r for FPU %i is not valid!" % (serialnumber, key)
            )

    # get sets of measured and evaluated FPUs
    fpu_config, measure_fpuset, eval_fpuset = get_sets(env, vfdb, fconfig, opts)

    return fpu_config, sorted(measure_fpuset), sorted(eval_fpuset)


def check_sns_unique(ctx):
    if not ctx.opts.reuse_serialnum:
        config_sns = set(
            [ctx.fpu_config[fpu_id]["serialnumber"] for fpu_id in ctx.measure_fpuset]
        )
        used_sns = get_snset(ctx.env, ctx.vfdb, ctx.opts)
        reused_sns = config_sns & used_sns
        print(
            "config_sns=%r, used_sns=%r, reused_sns=%r"
            % (config_sns, used_sns, reused_sns)
        )
        if reused_sns:
            raise ValueError(
                "serial numbers %s have been used before"
                " - use option '--reuse-serialnum' to explicitly"
                " use them again" % sorted(reused_sns)
            )
