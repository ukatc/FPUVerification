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



def check_connection(args, name, address):
    print("testing connection to %s .." % name, end='')
    flush()
    
    pok = check_ping_ok(address)
    if not pok:
        raise AssertionError("network connection to %s at address %r not alive" % (name, address))
    else:
        print("... OK")


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
