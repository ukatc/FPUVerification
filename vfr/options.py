from __future__ import absolute_import, division, print_function

import argparse
import re
import sys
import types
import warnings
from ast import literal_eval
from os import environ
import logging

from fpu_constants import (
    ALPHA_MIN_DEGREE,
    ALPHA_MAX_DEGREE,
    BETA_MIN_DEGREE,
    BETA_MAX_DEGREE,
)
from vfr.tests_common import lit_eval_file
from vfr.conf import DEFAULT_TASKS, DEFAULT_TASKS_NONFIBRE
from vfr.db.snset import get_snset
from vfr.helptext import examples, summary
from vfr.task_config import USERTASKS, MEASUREMENT_TASKS, T


def parse_args():
    try:
        DEFAULT_LOGLEVEL = int(environ.get("VFR_LOGLEVEL", str(logging.INFO)))
    except:
        print("VFR_LOGLEVEL has invalid value, setting level to INFO")
        DEFAULT_LOGLEVEL = logging.INFO

    parser = argparse.ArgumentParser(
        description=summary.format(DEFAULT_TASKS=DEFAULT_TASKS, **T.__dict__),
        epilog=examples.format(DEFAULT_TASKS=DEFAULT_TASKS, **T.__dict__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "tasks",
        nargs="*",
        default=[],
        help="""list of tasks to perform (default: %(default)s)""",
    )

    parser.add_argument(
        "-f",
        "--setup-file",
        default="",
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
        "-x",
        "--expand-tasks",
        default=False,
        action="store_true",
        help="expand and print given tasks and exit",
    )

    parser.add_argument(
        "-fmt",
        "--report-format",
        default="terse",
        choices=["status", "brief", "terse", "complete", "long", "extended", "csv"],
        help="""output format of 'report' task (one of 'status', 'terse', 'complete', 'long',
        'extended', 'csv', default is 'terse'). The options do the following:

        'status': print a single line with the overall status for each FPU
        'brief' : print one line for each test section
        'terse' : print essential information
        'complete' : print additional information, like angles with maximum errors
        'long'  : in addition, list values for each angle
        'extended' : print nearly full information, including a list of images
        'csv'   : produce a comma-separated export format which can be included in
                  spreadsheets. See option "-o" for storing the report into an output file.
        """,
    )

    parser.add_argument(
        "-sel",
        "--plot-selection",
        default="ABCDE",
        type=str,
        help="""Selection of plots
        A) dat_rep scatter plot in (x,y) image plane,
        B) pos_rep scatter plot,
        C) plot fitted pos_rep data (raw data and fits)
        D) plot raw data, fits, and fitted circle
        E) plot measured points vs. expected points from inverse calibration
        """,
    )

    parser.add_argument(
        "-blb",
        "--blob-type",
        choices=["small", "large"],
        default="large",
        type=str,
        help="""blob type selected for plotting, one of "small" or "large" """,
    )

    parser.add_argument(
        "-m",
        "--mockup",
        default=False,
        action="store_true",
        help="set gateway address to use mock-up gateway and FPU",
    )

    parser.add_argument(
        "-ign",
        "--ignore-analysis-failures",
        default=False,
        action="store_true",
        help="in the self-test, ignore image analysis failures "
        "(converting them into a warning)",
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
        "-awr",
        "--always-reset-fpus",
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
        help="""apply tasks only to passed set of serial numbers, passed alternatively as a
        python literal like this: "['MP001', 'MP002', ...]",
        a list, as in "PT01,PT02", or just as single serial number, as 'MP001'. A leading "~"
        indicates that the following string is a regular expression. For example,
        "~PT0[123][0-9]" matches the serial numbers PT010 to PT019, PT020 to PT029, and so on. """,
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
        help="repeat tests which were already passed successfully (except limit tests)",
    )

    parser.add_argument(
        "-rpl",
        "--repeat-limit-tests",
        default=False,
        action="store_true",
        help="repeat limit tests which were already passed successfully",
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
        help="reinitialize position database entry",
    )

    parser.add_argument(
        "-sf",
        "--skip-fibre",
        default=True,
        action="store_true",
        dest="skip_fibre",
        help="skip measurements and dependencies which require fibres to be present (default: %(default)s)",
    )

    parser.add_argument(
        "-mf",
        "--measure-fibre",
        default=True,
        action="store_false",
        dest="skip_fibre",
        help="explicitly perform measurements and dependencies which require fibres to be present",
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
        "-moe",
        "--mail-on-error",
        metavar="MAIL_ON_ERROR",
        type=str,
        default="",
        help="Email address of a user to which reports on critical errors are sent to. (default: %(default)r)",
    )

    parser.add_argument(
        "-N",
        "--NUM_FPUS",
        metavar="NUM_FPUS",
        dest="N",
        type=int,
        default=5,
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
        "-L",
        "--loglevel",
        metavar="LOGLEVEL",
        type=int,
        default=DEFAULT_LOGLEVEL,
        help="logging level. Set level to 30 to only show warnings and errrors. "
        "(can also be set by environment variable VFR_LOGLEVEL, default: %(default)s)",
    )

    parser.add_argument(
        "-clr",
        "--colorize",
        default=True,
        action="store_true",
        help="show success/failure report fields in colors",
    )

    args = parser.parse_args()

    if args.list_tasks:
        print("available tasks in alphabetic order: %r" % sorted(list(USERTASKS)))
        sys.exit(0)

    if len(args.tasks) == 0:
        if args.skip_fibre:
            args.tasks = DEFAULT_TASKS_NONFIBRE
        else:
            args.tasks = DEFAULT_TASKS

    if args.mockup:
        args.gateway_address = "127.0.0.1"
        args.gateway_port = 4700
        if args.setup_file:
            args.setup_file = "mock-" + args.setup_file

    if args.output_file is None:
        args.output_file = sys.stdout
    else:
        args.output_file = open(args.output_file, "w")

    db_opts = argparse.Namespace(
        **{
            k: vars(args)[k]
            for k in [
                "mockup",
                "report_format",
                "loglevel",
                "re_initialize",
                "output_file",
                "reuse_serialnum",
                "update_protection_limits",
                "protection_tolerance",
                "plot_selection",
                "blob_type",
                "display_alpha_max",
                "display_alpha_min",
                "display_beta_max",
                "display_beta_min",
                "record_count",
                "colorize",
            ]
        }
    )

    rig_opts = argparse.Namespace(
        **{
            k: vars(args)[k]
            for k in [
                "gateway_address",
                "gateway_port",
                "loglevel",
                "mockup",
                "manual_lamp_control",
                "always_reset_fpus",
                "re_initialize",
                "repeat_passed_tests",
                "repeat_limit_tests",
                "skip_fibre",
                "N",
                "bus_repeat_dummy_delay",
                "ignore_analysis_failures",
            ]
        }
    )

    return args, db_opts, rig_opts


sn_pat = re.compile("[a-zA-Z0-9]{1,5}$")

def expand_set(eval_snset, fpu_config, all_serial_numbers):

    if eval_snset == "all":
        # get the serial numbers of all FPUs which have been measured so far
        eval_snset = all_serial_numbers
        # this is a workaround against dirty data
        eval_snset = set(filter(lambda x: type(x) == types.StringType, eval_snset))
        fpu_config = {}
    else:
        if eval_snset is not None:
            # in this case, it needs to be a literal list of serial numbers,
            # a string with a quoted string literal, or a string
            try:
                vals = literal_eval(eval_snset)
            except (ValueError,SyntaxError):
                vals = eval_snset.split(",")

            if type(vals) != types.ListType:
                vals = [vals]

            expanded_vals = []
            for v in vals:
                if len(v) > 0:
                    if v[0] != '~':
                        expanded_vals.append(v)
                    else:
                        pat = re.compile(v[1:])
                        for sn in all_serial_numbers:
                            if pat.match(sn):
                                expanded_vals.append(sn)

            eval_snset = set(expanded_vals)

            # check passed serial numbers for validity
            for sn in eval_snset:
                if not sn_pat.match(sn):
                    raise ValueError("serial number %r is not valid!" % sn)

    return eval_snset, fpu_config

def get_sets(all_serial_numbers, fpu_config, opts):
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
    eval_snset, fpu_config = expand_set(opts.snset, fpu_config, all_serial_numbers)

    if eval_snset is None:
        # both mesured and evaluated sets are exclusively defined by
        # the measurement configuration file
        if set(opts.tasks) & MEASUREMENT_TASKS:
            # in this case, no measurements are needed,
            # which means that we do not need to access
            # protected resources like hardware or logfiles.
            measure_fpuset = set(fpu_config.keys())
            eval_fpuset = measure_fpuset
        else:
            measure_fpuset = set()
            eval_fpuset = fpu_config.keys()
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

        if set(opts.tasks) & MEASUREMENT_TASKS:
            measure_fpuset = set(measure_config.keys())
        else:
            measure_fpuset = set()

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
            warnings.warn(
                "Subset selected. Adjusting number of addressed FPUs to %i." % N
            )
            opts.N = N

    return fpu_config, sorted(measure_fpuset), sorted(eval_fpuset)


def check_config_item(fpu_id, val):
    try:
        key = int(fpu_id)
    except ValueError:
        raise ValueError("FPU identifier %r is not valid!" % fpu_id)

    if (key < 0) or (key > 4):
        raise ValueError("FPU id %i is not valid!" % key)

    serialnumber = val["serialnumber"]
    if not sn_pat.match(serialnumber):
        raise ValueError(
            "serial number %r for FPU %i is not valid!" % (serialnumber, key)
        )

def get_id(entry):
    if "fpu_id" in entry:
        return entry["fpu_id"]
    else:
        return (entry["can_id"] - 1)

def load_config(config_file_name):
    logger = logging.getLogger(__name__)
    if not config_file_name:
        # no measurement configuration
        logger.info("no measurement configuration passed")
        return {}

    logger.info("reading measurement configuratiom from %r..." % config_file_name)
    cfg_list = lit_eval_file(config_file_name)

    fconfig = dict(
        [
            (
                get_id(entry),
                {
                    "serialnumber": entry["serialnumber"],
                    "pos": entry["pos"],
                    "fpu_id": get_id(entry),
                },
            )
            for entry in cfg_list
        ]
    )

    for key, val in fconfig.items():
        check_config_item(key, val)

    return fconfig


def load_config_and_sets(all_serial_numbers, config_file_name, opts=None):

    fconfig = load_config(config_file_name)

    # get sets of measured and evaluated FPUs
    fpu_config, measure_fpuset, eval_fpuset = get_sets(
        all_serial_numbers, fconfig, opts
    )

    return fpu_config, sorted(measure_fpuset), sorted(eval_fpuset)


def check_sns_unique(rig, dbe):
    logger = logging.getLogger(__name__)
    if not dbe.opts.reuse_serialnum:
        config_sns = set(
            [rig.fpu_config[fpu_id]["serialnumber"] for fpu_id in rig.measure_fpuset]
        )
        used_sns = get_snset(dbe.env, dbe.vfdb, dbe.opts)
        reused_sns = config_sns & used_sns
        logger.debug(
            "config_sns=%r, used_sns=%r, reused_sns=%r"
            % (config_sns, used_sns, reused_sns)
        )
        if reused_sns:
            raise ValueError(
                "serial numbers %s have been used before"
                " - use option '--reuse-serialnum' to explicitly"
                " use them again" % sorted(reused_sns)
            )
