from __future__ import print_function, division

import os

import FpuGridDriver
from FpuGridDriver import (TEST_GATEWAY_ADRESS_LIST, GatewayAddress,
                           SEARCH_CLOCKWISE, SEARCH_ANTI_CLOCKWISE,
                           DEFAULT_WAVEFORM_RULSET_VERSION, DATUM_TIMEOUT_DISABLE)

from vfr.tests_common import flush


def check_ping_ok(ipaddr):
    rv = os.system('ping -q -c 1 -W 3 >/dev/null %s' % ipaddr)
    return rv == 0



def check_gateway_connection(args):
    print("testing connection to gateway..", end='')
    flush()
    
    pok = check_ping_ok(args.gateway_address)
    if not pok:
        raise AssertionError("network connection to gateway address not alive")
    else:
        print("... OK")


##  def initialize_FPU(args):
##      
##      gd = FpuGridDriver.GridDriver(args.N,
##                                    motor_minimum_frequency=args.min_step_frequency,  
##                                    motor_maximum_frequency=args.max_step_frequency, 
##                                    motor_max_start_frequency=args.max_start_frequency,
##                                    motor_max_rel_increase=args.max_acceleration)
##  
##          
##      gateway_address = [ GatewayAddress(args.gateway_address, args.gateway_port) ]
##  
##      print("connecting grid:", gd.connect(address_list=gateway_address))
##  
##      grid_state = gd.getGridState()
##  
##      return grid_state
##  

def init_driver(args, max_id, protected=True):
    if protected:
        rd = FpuGridDriver.GridDriver(max_id+1)
    else:
        rd = FpuGridDriver.UnprotectedGridDriver(max_id+1)

    gateway_adr = [ FpuGridDriver.GatewayAddress(args.gateway_address, args.gateway_port) ]

    print("connecting grid:", rd.connect(address_list=gateway_adr))

    grid_state = rd.getGridState()
    
    return rd, grid_state


def check_can_connection(rd, grid_state, args, fpu_id):
    print("checking CAN connection to FPU %i ..." % fpu_id, end='')
    flush()
            
    rv = rd.pingFPUs(grid_state, fpuset=[fpu_id])
    print(rv)
        
    return rv == FpuGridDriver.ethercanif.DE_OK


def ping_fpus(gd, grid_state, args):    
    
    gd.pingFPUs(grid_state)
    

    if args.resetFPUs:
        print("resetting FPUs")
        gd.resetFPUs(grid_state)
        print("OK")

    return grid_state
