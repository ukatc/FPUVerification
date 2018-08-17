#!/usr/bin/python

from __future__ import absolute_import,  print_function
import sys

from os import path
from ast import literal_eval
import argparse


import time
#import pylibftdi
import pyAPT
from pylibftdi import FtdiError


"""Thorlabs motor control, re-written in Python. 
To automatically use a certain device type with a specific
serial number, edit ${HOME}/.motorcontrolrc.

Commands:

info                   [serialnumber]            - print list of available serial devices
                                                   and movement units

status [-T devicetype] serialnumber              - retrieve and print status of device

home [-T devicetype] [-s speed] [-d direction={cw,acw}] [-l switch selection] serialnumber
                                                 - home device
                                                   (may require correct limit switch settings)

identify [-T devicetype]  serialnumber           - identify device by flashing LED

getpos [-T devicetype]  serialnumber             - get position 

moveabs [-T devicetype]  serialnumber  pos       - move absolute to pos

moverel [-T devicetype]  serialnumber  distance  - move relative to current pos
                                               
stop  [-T devicetype] serialnumber [--fast  ]    - stop motor (with '-p': in profiled mode)
"""

# this variable lists driver classes
from pyAPT.lts300 import LTS300
from pyAPT.mts50 import MTS50
from pyAPT.nr360s import NRS360S
from pyAPT.prm1 import PRM1
from pyAPT.cr1z7 import CR1Z7

driverlist = [LTS300, MTS50, NRS360S, PRM1, CR1Z7]

driver_map = { (str(d), d) for d in driverlist }
print("drivermap=", drivermap)

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    
    parser.add_argument('-T', '--devicetype', type=string, dest="devicetype",
                        default = os.env.get("THORLABS_DEFAULT_DEVICE", "MTS50"),
                        help="""Type of device driver which will be loaded. The default is
                        set by the environment variable THORLABS_DEFAULT_DEVICE.
                        To avoid setting the type each time the programm is called,
                        add the serial number / device mapping to the file
                        ${HOME}/.motorcontrolrc
                        """)
    
    parser.add_argument('-s', '--speed', dest='speed',  type=int,
                        default=10,
                        help='set speed in device units per seconds')
    
    parser.add_argument('-d', '--home-direction', dest='home_direction', 
                        default="to_zero",
                        help='direction of homing operation. Might not be applicable for a given stage.')

    
    args = parser.parse_args()
    
    return args


def get_devicetypes():
    homedir = path.expanduser(os.env.get("HOME", "~"))
    print("user homedir=",homedir)
    try:
        rcpath = path.join(homedir, ".motorcontrolrc")
        typedict = literal_eval(os.open(rcpath).readlines())
    except OSerror, e:
        print("warning: using default device type configuration")
        
    print("typedict:", repr(typedict))
    return typedict

    

def main():
    args = parse_args()
   
    if (len(args) < 4) or (
            (len(args) < 5) and (args[2] not in ["moveabs", "moverel"])) :
        print(__doc__)
        return 1

    command = args[2]
    try:
        serial = args[3]
    except IndexError:
        serial = None
      
    if len(args) > 4:
        dist = float(args[3])

        if serial == None:
            driver = Controller()
        else:
            dtypes = get_devicetypes()
            device_name = dtypes[serial]
            driver = driver_map[device_name](serial_number=serial)

    if command == "moverel":
      
        try:
            with driver as con:
                print('Found APT controller S/N',serial)
                print('\tMoving stage by %.3f %s ...'%(dist, con.unit), end=' ')
                con.move(dist)
                print('moved')
                print('\tNew position: %.3f %s'%(con.position(), con.unit))
                return 0
        except FtdiError as ex:
            print('\tCould not find APT controller S/N of',serial)
            return 1
        
    return 0


if __name__ == '__main__':
    sys.exit(main())
