from __future__ import print_function, division

import argparse
import sys
from os import environ

from ast import literal_eval
import re


from fpu_constants import *

from vfr.conf import DEFAULT_TASKS

# from vfr.tasks import *

from vfr.db.snset import get_snset

from helptext import summary


def parse_args():
    try:
        DEFAULT_VERBOSITY = int(environ.get("VFR_VERBOSITY", "0"))
    except:
        print ("VFR_VERBOSITY has invalid value, setting verbosity to one")
        DEFAULT_VERBOSITY = 1

    parser = argparse.ArgumentParser(description=summary)

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
        "-F",
        "--report-format",
        default="terse",
        choices=["terse", "long", "extensive"],
        help="output format of 'report' task (one of 'terse', 'long', 'extensive', default is 'terse')",
    )

    parser.add_argument(
        "-m",
        "--mockup",
        default=False,
        action="store_true",
        help="set gateway address to use mock-up gateway and FPU",
    )

    parser.add_argument(
        "-M",
        "--manual-lamp-control",
        default=False,
        action="store_true",
        help="switch to manual lamp control",
    )

    parser.add_argument(
        "-r",
        "--resetFPUs",
        default=False,
        action="store_true",
        help="reset all FPUs so that earlier aborts / collisions are ignored",
    )

    parser.add_argument(
        "-ra",
        "--alwaysResetFPUs",
        default=False,
        action="store_true",
        help="reset FPUs between each step of functional tests so that previous aborts / collisions are ignored",
    )

    parser.add_argument(
        "-R",
        "--re-initialize",
        default=False,
        action="store_true",
        help="re-initialize FPU counters even if entry exists",
    )

    parser.add_argument(
        "-S",
        "--snset",
        default=None,
        help="""apply tasks only to passed set of serial numbers, passed as "['MP001', 'MP002', ...]" """,
    )

    parser.add_argument(
        "-o",
        "--output-file",
        default=None,
        type=str,
        help="output file for report and dump (defaults to stdout)",
    )

    parser.add_argument(
        "-s",
        "--reuse-serialnum",
        default=False,
        action="store_true",
        help="reuse serial number",
    )

    parser.add_argument(
        "-p",
        "--repeat-passed-tests",
        default=False,
        action="store_true",
        help="repeat tests which were already passed successfully",
    )

    parser.add_argument(
        "-u",
        "--update-protection-limits",
        default=False,
        action="store_true",
        help="update range limits to protection database, even if already set",
    )

    parser.add_argument(
        "-t",
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
        "-w",
        "--rewind_fpus",
        default=False,
        action="store_true",
        help="rewind FPUs to datum position at start",
    )

    parser.add_argument(
        "-g",
        "--gateway_port",
        metavar="GATEWAY_PORT",
        type=int,
        default=4700,
        help="EtherCAN gateway port number (default: %(default)s)",
    )

    parser.add_argument(
        "-a",
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
        "-D",
        "--bus-repeat-dummy-delay",
        metavar="BUS_REPEAT_DUMMY_DELAY",
        type=int,
        default=2,
        help="Dummy delay inserted before writing to the same bus (default: %(default)s).",
    )

    parser.add_argument(
        "--alpha_min",
        metavar="ALPHA_MIN",
        type=float,
        default=ALPHA_MIN_DEGREE,
        help="minimum alpha value  (default: %(default)s)",
    )

    parser.add_argument(
        "--alpha_max",
        metavar="ALPHA_MAX",
        type=float,
        default=ALPHA_MAX_DEGREE,
        help="maximum alpha value  (default: %(default)s)",
    )

    parser.add_argument(
        "--beta_min",
        metavar="BETA_MIN",
        type=float,
        default=BETA_MIN_DEGREE,
        help="minimum beta value  (default: %(default)s)",
    )

    parser.add_argument(
        "--beta_max",
        metavar="BETA_MAX",
        type=float,
        default=BETA_MAX_DEGREE,
        help="maximum beta value  (default: %(default)s)",
    )

    parser.add_argument(
        "-v",
        "--verbosity",
        metavar="VERBOSITY",
        type=int,
        default=3,
        help="verbosity level of progress messages (default: %(default)s)",
    )

    args = parser.parse_args()

    if len(args.tasks) == 0:
        args.tasks = DEFAULT_TASKS

    if args.mockup:
        args.gateway_address = "127.0.0.1"
        args.gateway_port = 4700

    if not (args.snset is None):
        args.snset = literal_eval(args.snset)

    if args.output_file is None:
        args.output_file = sys.stdout
    else:
        args.output_file = open(args, output_file, "w")

    return args


def get_sets(vfdb, fpu_config, opts):
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
        eval_snset = get_snset(env, vfdb)
    elif eval_snset is not None:
        # in this case, it needs to be a list of serial numbers
        eval_snset = set(eval_snset)

    # check passed serial numbers for validity
    for sn in eval_snset:
        if not sn_pat.match(sn):
            raise ValueError("serial number %r is not valid!" % sn)

    if eval_snset is None:
        # both mesured and evaluated sets are exclusively defined by
        # the measurement configuration file
        measure_fpuset = fpu_config.keys()
        eval_fpuset = fpuset
    else:
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

        measure_fpuset = fpu_config.keys()

        extra_eval_sns = requested_snset.difference(measure_sns)

        # we use the serial numbers as key - these need not to have
        # integer type as they are not used in measurements.

        fpu_config = {sn: {"serialnumber": sn} for sn in extra_eval_sns}

        fpu_config.update(measure_config)

        eval_fpuset = fpu_config.keys()

    return fpu_config, sorted(measure_fpuset), sorted(eval_fpuset)

    # get sets of measured and evaluated FPUs
    fpu_config, measure_fpuset, eval_fpuset = get_sets(vfdb, fpu_config, opts)


sn_pat = re.compile("[a-zA-Z0-9]{1,5}$")


def get_sets(vfdb, fpu_config, opts):
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
        eval_snset = get_snset(env, vfdb)
    elif eval_snset is not None:
        # in this case, it needs to be a list of serial numbers
        eval_snset = set(eval_snset)

    # check passed serial numbers for validity

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

        measure_fpuset = fpu_config.keys()

        extra_eval_sns = requested_snset.difference(measure_sns)

        # we use the serial numbers as key - these need not to have
        # integer type as they are not used in measurements.

        fpu_config = {sn: {"serialnumber": sn} for sn in extra_eval_sns}

        fpu_config.update(measure_config)

        eval_fpuset = fpu_config.keys()

    return fpu_config, measure_fpuset, eval_fpuset


def load_config(config_file_name, vfdb, opts):
    print ("reading measurement configuratiom from %r..." % config_file_name)
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
    fpu_config, measure_fpuset, eval_fpuset = get_sets(vfdb, fconfig, opts)

    return fpu_config, sorted(measure_fpuset), sorted(eval_fpuset)
