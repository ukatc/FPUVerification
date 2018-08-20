#!/usr/bin/python

from __future__ import absolute_import,  print_function
import sys

from os import path, environ
from ast import literal_eval
import argparse


import time
#import pylibftdi
import pyAPT
from pylibftdi import FtdiError
from pylibftdi import Driver as LibFTDI_Driver


"""Thorlabs motor control, re-written in Python. 
To automatically use a certain device type with a specific
serial number, edit ${HOME}/.motorcontrolrc.

Commands:

info                   [serialnumber]            - print list of available serial devices
                                                   and movement units. if serialnumber is given,
                                                   this is restricted to the device with that number.

status [-T devicetype] serialnumber              - retrieve and print status of device

get_velparams [-T devicetype] serialnumber       - retrieve and print velocity parameters

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
from pyAPT.controller import Controller # the generic diver class

from pyAPT.lts300 import LTS300
from pyAPT.mts50 import MTS50
from pyAPT.nr360s import NR360S
from pyAPT.prm1 import PRM1
from pyAPT.cr1z7 import CR1Z7

driverlist = [LTS300, MTS50, NR360S, PRM1, CR1Z7]

driver_map = dict([(d.__name__, d) for d in driverlist ])

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('command', type=str, nargs='?',
                        default="info",
                        help='command')
    
    parser.add_argument('serialnum', metavar='S', type=int, nargs='?',
                        default=None,
                        help='serial number of device')

    parser.add_argument('distance', metavar='N', type=float, nargs='?',
                        help='new position or movement distance')

    parser.add_argument('-T', '--devicetype', type=str, dest="devicetype",
                        default = environ.get("THORLABS_DEFAULT_DEVICE", "MTS50"),
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
                        default=None,
                        help='direction of homing operation. Might not be applicable for a given stage.')

    parser.add_argument('-m', '--monitor_completion', dest='monitor_completion', 
                        default=False, action="store_true",
                        help='print info on command execution until it is completed.')

    
    args = parser.parse_args()
    
    return args


def get_devicetypes():
    homedir = path.expanduser(environ.get("HOME", "~"))
    try:
        rcpath = path.join(homedir, ".thorlabs_motorcontrolrc")
        cfg = "".join(open(rcpath).readlines())
        typedict = literal_eval(cfg)
    except IOError, e:
        print("warning: configuration file %r not found,  using default device type configuration" % rcpath)
        typedict = { 83822910 : 'MTS50',
                     40873952 : 'NR360S' }	

        
    #print("typedict:", repr(typedict))
    return typedict

def print_device_info(driver):
    with driver as con:
        info = con.info()
        print('\tController info:')
        labels=['S/N','Model','Type','Firmware Ver', 'Notes', 'H/W Ver',
                'Mod State', 'Channels']

        for idx,ainfo in enumerate(info):
            print('\t%12s: %s'%(labels[idx], bytes(ainfo)))

def list_device_info():
    # no serial number given, we retrieve a list of all devices
    print("getting low-level driver")
    drv = LibFTDI_Driver()
    print("getting device list")
    controllers = drv.list_devices()
    print ("device list = ", repr(controllers))

    if controllers:
        for vendor, devicetype, serialnumber in controllers:
            print('Found %s %s S/N: %s'% (vendor, devicetype, serialnumber))
            driver = pyAPT.Controller(serial_number=serialnumber)
            print_device_info(driver)
    else:
        print("no Thorlabs / FTDI controllers found")
        return 1
    
def exec_moverel(driver, serialnum, dist):
    if dist is None:
        print("Error: distance parameter is missing! Exiting without move.")
        return 1

  
    try:
        with driver as con:
            print('Found APT controller S/N',serialnum)
            print('\tMoving stage by %.3f %s ...'%(dist, con.unit), end=' ')
            con.move(dist)
            print('moved')
            print('\tNew position: %.3f %s'%(con.position(), con.unit))
            return 0
    except FtdiError as ex:
        print('\tCould not find APT controller S/N of',serialnum)
        return 1

def auto_detect_driverclass(serialnum):
    if serialnum != None:
        dtypes = get_devicetypes()
        device_name = dtypes[serialnum]
        driverclass = driver_map[device_name](serial_number=serialnum)
        return driverclass

def exec_get_position(driver, serialnum):
    with driver as con:
        print('\tPosition (%s) = %.2f [enc:%d]'%(con.unit,
                                                 con.position(),
                                                con.position(raw=True)))
    return 0

def exec_get_status(driver, serialnum):
    with driver as con:
        status = con.status()
        print('\tController status:')
        print('\t\tPosition: %.3fmm (%d cnt)'%(status.position, status.position_apt))
        print('\t\tVelocity: %.3fmm'%(status.velocity))
        print('\t\tStatus:',status.flag_strings())


def exec_get_velparams(driver, serialnum):
    with driver as con:
        min_vel, acc, max_vel = con.velocity_parameters()
        raw_min_vel, raw_acc, raw_max_vel = con.velocity_parameters(raw=True)
        print('\tController velocity parameters:')
        print('\t\tMin. Velocity: %.2fmm/s (%d)'%(min_vel, raw_min_vel))
        print('\t\tAcceleration: %.2fmm/s/s (%d)'%(acc, raw_acc))
        print('\t\tMax. Velocity: %.2fmm/s (%d)'%(max_vel, raw_max_vel))

def exec_moveabs(driver, serialnum, newposition, wait=True):
    try:
        with driver as con:
            print('Found APT controller S/N',serialnum)
            print('\tMoving stage to %.2f %s...'%(newposition, con.unit))
            st=time.time()
            con.goto(newposition, wait=wait)
            if not wait:
                stat = con.status()
                while stat.moving:
                    out = '        pos %3.2f %s vel %3.2f %s/s'%(stat.position, con.unit,
                                                                 stat.velocity, con.unit)
                    sys.stdout.write(out)
                    time.sleep(0.01)
                    stat=con.status()
                    l = len(out)
                    sys.stdout.write('\b'*l)
                    sys.stdout.write(' '*l)
                    sys.stdout.write('\b'*l)
    
            print('\tMove completed in %.2fs'%(time.time()-st))
            print('\tNew position: %.2f %s'%(con.position(), con.unit))
            if not wait:
                print('\tStatus:',con.status())
            return 0
        
    except FtdiError as ex:
        print('\tCould not find APT controller S/N of',serial)
        return 1

def exec_home(driver, serialnum, home_direction=None):
    kwargs = {}
    if home_direction == "to_zero":
        kwargs["to_zero"]=True
    elif home_direction == "clockwise":
        kwargs["clockwise"]=True
    elif home_direction == "anticlockwise":
        kwargs["clockwise"]=False
    elif home_direction == "to_positive":
        kwargs["to_zero"]=False
        
    with driver as con:
        print('\tHoming stage...', end=' ')
        sys.stdout.flush()
        con.home(**kwargs)
        
    print('OK')

    
def main():
    args = parse_args()
   
    command = args.command
    serialnum = args.serialnum
    dist = args.distance

    if command=="help":
        print(__doc__)
        return 1
      
    driver = auto_detect_driverclass(serialnum)
    
    if command == "info":

        if serialnum != None:
            return print_device_info(driver)

        return list_device_info()
    
    elif command == "get_position":
        return exec_get_position(driver, serialnum)
    
    elif command == "get_status":
        return exec_get_status(driver, serialnum)
        
    elif command == "get_velparams":
        return exec_get_velparams(driver, serialnum)
        
    elif command == "moverel":
        return exec_moverel(driver, serialnum, dist)
    
    elif command == "moveabs":
        return exec_moveabs(driver, serialnum, dist, wait=not args.monitor_completion)
    
    elif command == "home":
        return exec_home(driver, serialnum, home_direction=args.home_direction)
    else:
        raise ValueError("command not recognized")

        
    return 0


if __name__ == '__main__':
    sys.exit(main())
