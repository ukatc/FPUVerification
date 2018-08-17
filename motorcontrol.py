#!/usr/bin/python

from __future__ import absolute_import
from __future__ import print_function
import argparse

import time
import pylibftdi
import pyAPT

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
                                               
stop  [-T devicetype] [--fast  ]                 - stop motor (with '-p': in profiled mode)
"""

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    
    parser.add_argument('-T', '--devicetype' metavar='T', type=string, dest="devicetype",
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



def main(args):
  if len(args)<3:
    print(__doc__)
    return 1
  else:
    serial = args[1]
    dist = float(args[2])

  try:
    with pyAPT.NR360S(serial_number=serial) as con:
      print('Found APT controller S/N',serial)
      print('\tMoving stage by %.2fmm...'%(dist), end=' ')
      con.move(dist)
      print('moved')
      print('\tNew position: %.2f %s'%(con.position(), con.unit))
      return 0
  except pylibftdi.FtdiError as ex:
    print('\tCould not find APT controller S/N of',serial)
    return 1

if __name__ == '__main__':
  import sys
  sys.exit(main(sys.argv))



