#!/usr/bin/python

from __future__ import absolute_import, print_function

import argparse
import sys
import time
from ast import literal_eval
from os import environ, path

# import pylibftdi
import pyAPT

# from pyAPT.controller import Controller  # the generic diver class
from pyAPT.cr1z7 import CR1Z7
from pyAPT.lts300 import LTS300
from pyAPT.mts50 import MTS50
from pyAPT.nr360s import NR360S
from pyAPT.prm1 import PRM1
from pylibftdi import Driver as LibFTDI_Driver
from pylibftdi import FtdiError

__help__ = """Thorlabs motor control, re-written in Python.
To automatically use a certain device type with a specific
serial number, edit ${HOME}/.motorcontrolrc.

Commands:

info   [serialnum]                         - print list of available serial devices
                                             and movement units. if serialnum is given,
                                             this is restricted to the device with that number.

status [-T devtype] serialnum              - retrieve and print status of device (does not work with NR360)

identify [-T devtype]  serialnum           - identify device by flashing LED

getpos [-T devtype]  serialnum            - get position, in device units

getvelparams [-T devtype] serialnum       - retrieve and print velocity parameters

setvelparams [-T devtype] serialnum [-v velocity] [-a accel]  - set velocity parameters

home [-T devtype] [-v velocity] [-d direction={cw,acw}] [-l switch] serialnum
                                           - home device
                                             (depending on the weirdness of the particulatr controller,
                                              may require specific limit switch settings or even negative
                                              velocity).

moverel [-T devtype]  serialnum  distance  - move relative to current pos, (floating point number
                                             in device units).

moveabs [-T devtype]  [-m] serialnum  pos  - move absolute to pos. May not work with NR360 stage.

stop  [-T devtype] serialnum [--fast] [--nowait] - stop motor (with '--fast': in unprofiled mode)

reset  [-T devtype] serialnum              - reset controller to eprom defaults. This is untested
                                             and might have unintended consequences.

"""

# this variable lists driver classes


driverlist = [LTS300, MTS50, NR360S, PRM1, CR1Z7]

driver_map = dict([(d.__name__, d) for d in driverlist])


def parse_args():
    parser = argparse.ArgumentParser(
        description=__help__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("command", type=str, nargs="?", default="info", help="command")

    parser.add_argument(
        "serialnum",
        metavar="SERIALNUM",
        type=int,
        nargs="?",
        default=None,
        help="serial number of device",
    )

    parser.add_argument(
        "distance",
        metavar="PAR",
        type=float,
        nargs="?",
        help="new position or movement distance",
    )

    parser.add_argument(
        "-T",
        "--devicetype",
        type=str,
        dest="devicetype",
        default=environ.get("THORLABS_DEFAULT_DEVICE", "MTS50"),
        help="""Type of device driver which will be loaded. The default
                        can be set by the environment variable THORLABS_DEFAULT_DEVICE.
                        To avoid setting the type each time the programm is called,
                        add the serial number / device mapping to the file
                        ${HOME}/.motorcontrolrc .
                        """,
    )

    parser.add_argument(
        "-v",
        "--velocity",
        dest="velocity",
        type=float,
        default=10,
        help="set velocity, in device units per seconds",
    )

    parser.add_argument(
        "-a",
        "--acceleration",
        dest="acceleration",
        type=float,
        default=5,
        help="set acceleration in device units per seconds^2",
    )

    parser.add_argument(
        "-d",
        "--home-direction",
        dest="home_direction",
        default=None,
        help="""Direction of homing operation. Might not be applicable
                        for a given stage. Direction can be, e.g., 'to_zero',
                        'clockwise', 'anticlockwise', 'to_positive' - depends on driver.
                        Note: If it doesn't work, try to set the velocity"
                        to a negative value.""",
    )

    parser.add_argument(
        "-l",
        "--limitswitch",
        dest="limitswitch",
        default=None,
        help="Limit switch flag. See protocol documentation of home"
        " commmand for more info. Might not work as described.",
    )

    parser.add_argument(
        "-m",
        "--monitor_completion",
        dest="monitor_completion",
        default=False,
        action="store_true",
        help="print progress info until moveabs command is completed"
        " (does *not* work with NR360 stage).",
    )

    parser.add_argument(
        "-n",
        "--nowait",
        dest="nowait",
        default=False,
        action="store_true",
        help="do not wait for stop command to complete.",
    )

    parser.add_argument(
        "-f",
        "--fast",
        dest="immediate_stop",
        default=False,
        action="store_true",
        help="When stopping, stop device abruptly, without"
        " slowing down before (aka unprofiled stop).",
    )

    args = parser.parse_args()

    return args


def get_devicetypes():
    homedir = path.expanduser(environ.get("HOME", "~"))
    try:
        rcpath = path.join(homedir, ".thorlabs_motorcontrolrc")
        cfg = "".join(open(rcpath).readlines())
        typedict = literal_eval(cfg)
    except IOError:
        print(
            "warning: configuration file %r not found,  using default device type configuration"
            % rcpath
        )
        typedict = {83822910: "MTS50", 40873952: "NR360S"}

    # print("typedict:", repr(typedict))
    return typedict


def print_device_info(driver):
    with driver as con:
        info = con.info()
        print("\tController info:")
        labels = [
            "S/N",
            "Model",
            "Type",
            "Firmware Ver",
            "Notes",
            "H/W Ver",
            "Mod State",
            "Channels",
        ]

        for idx, ainfo in enumerate(info):
            print("\t%12s: %s" % (labels[idx], bytes(ainfo)))


def list_device_info():
    # no serial number given, we retrieve a list of all devices
    drv = LibFTDI_Driver()
    controllers = drv.list_devices()

    if controllers:
        for vendor, devicetype, serialnumber in controllers:
            print("Found %s %s S/N: %s" % (vendor, devicetype, serialnumber))
            driver = pyAPT.Controller(serial_number=serialnumber)
            print_device_info(driver)
    else:
        print("no Thorlabs / FTDI controllers found")
        return 1


def exec_identify(driver, serialnum, wait_for_enter=True):
    with driver as con:
        print("\tIdentifying controller")
        con.identify()
        raw_input("\n>>>>Press enter to continue")


def exec_moverel(driver, serialnum, dist):
    if dist is None:
        print("Error: distance parameter is missing! Exiting without move.")
        return 1

    try:
        with driver as con:
            print("Found APT controller S/N", serialnum)
            print("\tMoving stage by %.3f %s ..." % (dist, con.unit), "end=''")
            con.move(dist)
            print("moved")
            print("\tNew position: %.3f %s" % (con.position(), con.unit))
            return 0
    except FtdiError:
        print("\tCould not find APT controller S/N of", serialnum)
        return 1


def auto_detect_driverclass(serialnum):
    if serialnum != None:
        dtypes = get_devicetypes()
        device_name = dtypes[serialnum]
        driverclass = driver_map[device_name](serial_number=serialnum)
        return driverclass


def exec_get_position(driver, serialnum):
    with driver as con:
        print(
            "\tPosition (%s) = %.2f [enc:%d]"
            % (con.unit, con.position(), con.position(raw=True))
        )
    return 0


def exec_get_status(driver, serialnum):
    with driver as con:
        status = con.status()
        print("\tController status:")
        print("\t\tPosition: %.3fmm (%d cnt)" % (status.position, status.position_apt))
        print("\t\tVelocity: %.3fmm" % (status.velocity))
        print("\t\tStatus:", status.flag_strings())


def exec_get_velparams(driver, serialnum):
    with driver as con:
        min_vel, acc, max_vel = con.velocity_parameters()
        raw_min_vel, raw_acc, raw_max_vel = con.velocity_parameters(raw=True)
        print("\tController velocity parameters:")
        print("\t\tMin. Velocity: %.2fmm/s (%d)" % (min_vel, raw_min_vel))
        print("\t\tMax. Velocity: %.2fmm/s (%d)" % (max_vel, raw_max_vel))
        print("\t\tAcceleration: %.2fmm/s/s (%d)" % (acc, raw_acc))


def exec_moveabs(driver, serialnum, newposition, wait=True, monitor=False):
    try:
        if monitor:
            wait = False
        with driver as con:
            print("Found APT controller S/N", serialnum)
            print("\tMoving stage to %.2f %s..." % (newposition, con.unit))
            st = time.time()
            con.goto(newposition, wait=wait)
            if monitor:
                stat = con.status()
                while stat.moving:
                    out = "        pos %3.2f %s vel %3.2f %s/s" % (
                        stat.position,
                        con.unit,
                        stat.velocity,
                        con.unit,
                    )
                    sys.stdout.write(out)
                    time.sleep(0.01)
                    stat = con.status()
                    l = len(out)
                    sys.stdout.write("\b" * l)
                    sys.stdout.write(" " * l)
                    sys.stdout.write("\b" * l)

            print("\tMove completed in %.2fs" % (time.time() - st))
            print("\tNew position: %.2f %s" % (con.position(), con.unit))
            if monitor:
                print("\tStatus:", con.status())
            return 0

    except FtdiError:
        print("\tCould not find APT controller S/N of", serialnum)
        return 1


def exec_home(driver, serialnum, home_direction=None, limitswitch=None, velocity=None):
    kwargs = {}
    if home_direction == "to_zero":
        kwargs["to_zero"] = True
    elif home_direction == "clockwise":
        kwargs["clockwise"] = True
    elif home_direction == "anticlockwise":
        kwargs["clockwise"] = False
    elif home_direction == "to_positive":
        kwargs["to_zero"] = False

    if limitswitch != None:
        kwargs["lswitch"] = limitswitch

    if velocity != None:
        kwargs["velocity"] = velocity

    with driver as con:
        print("\tHoming stage...", "end=''")
        sys.stdout.flush()
        con.home(**kwargs)

    print("OK")
    return 0


def exec_stop(driver, serialnum, immediate=False, wait=True):
    if immediate:
        mode = "immediate stop"
    else:
        mode = "profiled stop"

    try:
        print("stopping serial number %s (%s) ..." % (serialnum, mode), "end=' '")
        sys.stdout.flush()
        with driver as con:
            con.stop(immediate=True, wait=wait)
            print("STOPPED")

    except FtdiError as ex:
        print("\terror stopping device %s (%s)" % (serialnum, ex))
        return 1
    return 0


def exec_set_velparams(driver, serialnum, max_velocity=None, max_acceleration=None):
    assert max_velocity != None
    assert max_acceleration != None
    with driver as con:
        unit = con.unit
        print("\tSetting new velocity parameters", max_acceleration, max_velocity)
        con.set_velocity_parameters(float(max_acceleration), float(max_velocity))
        min_vel, acc, max_vel = con.velocity_parameters()
        print("\tNew velocity parameters:")
        print("\t\tMin. Velocity: %.2f %s" % (min_vel, unit))
        print("\t\tMax. Velocity: %.2f %s" % (max_vel, unit))
        print("\t\tAcceleration: %.2f %s" % (acc, unit))


def exec_reset(driver, serialnum):
    with driver as con:
        print("\tResetting controller parameters to EEPROM defaults")
        con.reset_parameters()
    return 0


def main():
    args = parse_args()

    command = args.command
    serialnum = args.serialnum
    dist = args.distance

    if command == "help":
        print(__help__)
        return 1

    driver = auto_detect_driverclass(serialnum)

    if command == "info":

        if serialnum != None:
            return print_device_info(driver)

        return list_device_info()

    elif command == "identify":
        return exec_identify(driver, serialnum, wait_for_enter=True)

    elif command == "getpos":
        return exec_get_position(driver, serialnum)

    elif command == "status":
        return exec_get_status(driver, serialnum)

    elif command == "getvelparams":
        return exec_get_velparams(driver, serialnum)

    elif command == "setvelparams":
        return exec_set_velparams(
            driver,
            serialnum,
            max_velocity=args.velocity,
            max_acceleration=args.acceleration,
        )

    elif command == "moverel":
        return exec_moverel(driver, serialnum, dist)

    elif command == "moveabs":
        return exec_moveabs(driver, serialnum, dist, monitor=args.monitor_completion)

    elif command == "stop":
        return exec_stop(
            driver, serialnum, immediate=args.immediate_stop, wait=(not args.nowait)
        )

    elif command == "home":
        return exec_home(
            driver,
            serialnum,
            home_direction=args.home_direction,
            velocity=args.velocity,
        )

    elif command == "reset":
        return exec_reset(driver, serialnum)
    else:
        raise ValueError("command not recognized")

    return 0


if __name__ == "__main__":
    sys.exit(main())
