#!/usr/bin/env python

from __future__ import print_function, division

import sys
import argparse
import re
import os
import ast
import platform

import lmdb

import FpuGridDriver
from FpuGridDriver import (TEST_GATEWAY_ADRESS_LIST, GatewayAddress,
                           SEARCH_CLOCKWISE, SEARCH_ANTI_CLOCKWISE,
                           DEFAULT_WAVEFORM_RULSET_VERSION, DATUM_TIMEOUT_DISABLE)
from fpu_commands import *
from fpu_constants import *

from interval import Interval
from protectiondb import ProtectionDB as pdb
from protectiondb import INIT_COUNTERS

from vfr.conf import DEFAULT_TASKS, ALPHA_DATUM_OFFSET


import lmdb
from interval import Interval
from protectiondb import ProtectionDB as pdb
from protectiondb import INIT_COUNTERS
from protectiondb import HealthLogDB

from fpu_constants import *

DATABASE_FILE_NAME = os.environ.get("FPU_DATABASE")

# needs 64 bit OS (specifically, large file support) for normal database size
if platform.architecture()[0] == "64bit":
    dbsize = 5*1024*1024*1024
else:
    dbsize = 5*1024*1024
    

def flush():
    sys.stdout.flush()

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


def initialize_FPU(args):
    
    gd = FpuGridDriver.GridDriver(args.N,
                                  motor_minimum_frequency=args.min_step_frequency,  
                                  motor_maximum_frequency=args.max_step_frequency, 
                                  motor_max_start_frequency=args.max_start_frequency,
                                  motor_max_rel_increase=args.max_acceleration)

        
    gateway_address = [ GatewayAddress(args.gateway_address, args.gateway_port) ]

    print("connecting grid:", gd.connect(address_list=gateway_address))

    grid_state = gd.getGridState()

    return grid_state


def ping_fpus(gd, grid_state, args):    
    
    gd.pingFPUs(grid_state)
    

    if args.resetFPUs:
        print("resetting FPUs")
        gd.resetFPUs(grid_state)
        print("OK")

    return grid_state


def rewind_fpus(gd, grid_state, args):

    # Now, we issue a findDatum method. In order to know when and how
    # this command finished, we pass the grid_state variable.

    if args.rewind_fpus:
        current_angles = gd.trackedAngles(grid_state, retrieve=True)
        current_alpha = array([x.as_scalar() for x, y in current_angles ])
        current_beta = array([y.as_scalar() for x, y in current_angles ])
        print("current positions:\nalpha=%r,\nbeta=%r" % (current_alpha, current_beta))
              
        if False :
              
            print("moving close to datum switch")
            wf = gen_wf(- current_alpha + 0.5, - current_beta + 0.5)
            gd.configMotion(wf, grid_state, allow_uninitialized=True)
            gd.executeMotion(grid_state)
            
    return grid_state

def find_datum(gd, grid_state, args):
    
    print("issuing findDatum:")
    gd.findDatum(grid_state, timeout=DATUM_TIMEOUT_DISABLE)
    print("findDatum finished")

    # We can use grid_state to display the starting position
    print("the starting position (in degrees) is:", list_angles(grid_state)[0])

    return gd, grid_state
 

def parse_args():
    parser = argparse.ArgumentParser(description='test FPUs in verification rig')
    
    parser.add_argument('tasks',  nargs='+',
                        default=DEFAULT_TASKS, 
                        help="""list of tasks to perform (default: %(default)s)""")
    
    parser.add_argument('-f', '--setup-file',   default="fpus.cfg", type=str,
                        help='FPU configuration')

    parser.add_argument('-m', '--mockup',   default=False, action='store_true',
                        help='set gateway address to use mock-up gateway and FPU')

    parser.add_argument('-r', '--resetFPUs',   default=False, action='store_true',
                        help='reset all FPUs so that earlier aborts / collisions are ignored')

    parser.add_argument('-R', '--re-initialize',   default=False, action='store_true',
                        help='re-initialize FPU counters even if entry exists')

    parser.add_argument('-s', '--reuse-serialnum', default=False, action='store_true',
                        help='reuse serial number')

    parser.add_argument('-i', '--reinit-db', default=False, action='store_true',
                        help='reinitialize posiiton database entry')

    parser.add_argument('-w', '--rewind_fpus', default=False, action='store_true',
                        help='rewind FPUs to datum position at start')

    parser.add_argument('-p', '--gateway_port', metavar='GATEWAY_PORT', type=int, default=4700,
                        help='EtherCAN gateway port number (default: %(default)s)')

    parser.add_argument('-a', '--gateway_address', metavar='GATEWAY_ADDRESS', type=str, default="192.168.0.10",
                        help='EtherCAN gateway IP address or hostname (default: %(default)r)')
    
    parser.add_argument('-N', '--NUM_FPUS',  metavar='NUM_FPUS', dest='N', type=int, default=6,
                        help='Number of adressed FPUs (default: %(default)s).')    
        
    parser.add_argument('-D', '--bus-repeat-dummy-delay',  metavar='BUS_REPEAT_DUMMY_DELAY',
                        type=int, default=2,
                        help='Dummy delay inserted before writing to the same bus (default: %(default)s).')        
            
    parser.add_argument('--alpha_min', metavar='ALPHA_MIN', type=float, default=ALPHA_MIN_DEGREE,
                        help='minimum alpha value  (default: %(default)s)')
    
    parser.add_argument('--alpha_max', metavar='ALPHA_MAX', type=float, default=ALPHA_MAX_DEGREE,
                        help='maximum alpha value  (default: %(default)s)')
    
    parser.add_argument('--beta_min', metavar='BETA_MIN', type=float, default=BETA_MIN_DEGREE,
                        help='minimum beta value  (default: %(default)s)')
    
    parser.add_argument('--beta_max', metavar='BETA_MAX', type=float, default=BETA_MAX_DEGREE,
                        help='maximum beta value  (default: %(default)s)')        

    parser.add_argument('-v', '--verbosity', metavar='VERBOSITY', type=int,
                        default=3,
                        help='verbosity level of progress messages (default: %(default)s)')
    
    
    args = parser.parse_args()
    
    if args.mockup:
        args.gateway_address = "127.0.0.1"
        args.gateway_port = 4700

    return args


def load_config(config_file_name):
    print("reading configuratiom from %r..." % config_file_name)
    cfg_list = ast.literal_eval(''.join(open(config_file_name).readlines()))

    fconfig = dict([ (entry['id'], { 'serialnumber' : entry['serialnumber'],
                                     'pos' : entry['pos'] }) for entry in cfg_list])

    sn_pat = re.compile('[a-zA-Z0-9]{1,5}$')
    for key, val in fconfig.items():
        if key < 0:
            raise ValueError("FPU id %i is not valid!" % key)
        serialnumber = val['serialnumber']
        if not sn_pat.match(serialnumber):
            raise ValueError("serial number %r for FPU %i is not valid!" % (serialnumber, key))

    
    return fconfig


def init_driver(args, max_id, protected=True):
    if protected:
        rd = FpuGridDriver.GridDriver(max_id+1)
    else:
        rd = FpuGridDriver.UnprotectedGridDriver(max_id+1)

    gateway_adr = [ FpuGridDriver.GatewayAddress(args.gateway_address, args.gateway_port) ]

    print("connecting grid:", rd.connect(address_list=gateway_adr))

    grid_state = rd.getGridState()
    
    return rd, grid_state


def check_can_connection(rd, args, fpu_id):
    print("checking CAN connection to FPU %i ..." % fpu_id, end='')
    flush()
            
    rv = rd.pingFPUs(grid_state, fpuset=[fpu_id])
    print(rv)
        
    return rv == FpuGridDriver.ethercanif.DE_OK



def init_position(env, fpudb, fpu_id, serialnumber, alpha_start, beta_start, re_initialize=True):
    sn = serialnumber
    
    aint = Interval(alpha_start)
    bint = Interval(beta_start)

    waveform_reversed = False
    
    init_counters = INIT_COUNTERS.copy()
        
    print("setting FPU #%i, sn=%s to starting position (%r, %r) ... " % (fpu_id, serialnumber,
                                                                                 alpha_start, beta_start), end='')
    flush()
    
    with env.begin(write=True,db=fpudb) as txn:
        if re_initialize:
            counters = None
        else:
            counters =  pdb.getRawField(txn, sn, pdb.counters)
            
        if counters != None:
            init_counters.update(counters)
            

        pdb.putInterval(txn, sn, pdb.alpha_positions, aint, ALPHA_DATUM_OFFSET)
        pdb.putInterval(txn, sn, pdb.beta_positions, bint, BETA_DATUM_OFFSET)
        pdb.putField(txn, sn, pdb.waveform_table, [])
        pdb.putField(txn, sn, pdb.waveform_reversed, waveform_reversed)
        pdb.putInterval(txn, sn, pdb.alpha_limits, Interval(ALPHA_MIN_DEGREE, ALPHA_MAX_DEGREE), ALPHA_DATUM_OFFSET)
        pdb.putInterval(txn, sn, pdb.beta_limits, Interval(BETA_MIN_DEGREE, BETA_MAX_DEGREE), BETA_DATUM_OFFSET)
        pdb.putField(txn, sn, pdb.free_beta_retries, DEFAULT_FREE_BETA_RETRIES)
        pdb.putField(txn, sn, pdb.beta_retry_count_cw, 0)
        pdb.putField(txn, sn, pdb.beta_retry_count_acw, 0)
        pdb.putField(txn, sn, pdb.counters, init_counters)

    print("OK")


def test_datum(gd, grid_state, args, fpuset):
    gd.pingFPUs(grid_state, fpuset=fpuset)

    # depending on options, we reset & rewind the FPUs
    if args.resetFPUs:
        print("resetting FPUs.... ", end='')
        flush()
        gd.resetFPUs(grid_state, fpuset=fpuset)
        print("OK")
    
    if args.rewind_fpus:
        current_angles = gd.trackedAngles(grid_state, retrieve=True)
        current_alpha = array([x.as_scalar() for x, y in current_angles ])
        current_beta = array([y.as_scalar() for x, y in current_angles ])
        print("current positions:\nalpha=%r,\nbeta=%r" % (current_alpha, current_beta))
              
        print("moving close to datum switch")
        wf = gen_wf(- current_alpha + 0.5, - current_beta + 0.5)
        wf = { k : v for k, v in wf.items() if k in fpuset }
        gd.configMotion(wf, grid_state, allow_uninitialized=True)
        gd.executeMotion(grid_state, fpuset=fpuset)
    
    
    # Now, we issue a findDatum method. In order to know when and how
    # this command finished, we pass the grid_state variable.
    
    print("issuing findDatum:")
    gd.findDatum(grid_state, timeout=DATUM_TIMEOUT_DISABLE, fpuset=fpuset)
    print("findDatum finished")

    
if __name__ == '__main__':
    print("starting verification")
    args = parse_args()
    print("tasks = %r" % args.tasks)

    for tsk in args.tasks:
        if tsk not in ["test_gateway_connection",
                       "test_can_connection",
                       "test_datum",
                       "test_alpha_max",
                       "test_beta_max",
                       "test_beta_min",
                       "test_functional",
                       "flash_snum",
                       "init",
                       "init_positions"]:
            
            raise ValueError("invalid task name '%s'" % tsk)
        
    
    if "init" in args.tasks:
        expansion = ["flash_snum",
                     "init_positions",]
        
        print("[expanding init] ###")
        print("...expanded to %r" % expansion)
        args.tasks.extend(expansion)
        
    if "test_functional" in args.tasks:
        expansion = ["test_gateway_connection",
                     "test_can_connection",
                     "test_datum",
                     "test_alpha_max",
                     "test_beta_max",
                     "test_beta_min"]
        
        print("[expanding test_functional] ###")
        print("...expanded to %r" % expansion)
        args.tasks.extend(expansion)

    if "test_gateway_connection" in args.tasks:
        print("[test_gateway_connection] ###")
        check_gateway_connection(args)

    fpu_config = load_config(args.setup_file)


    print("config= %r" % fpu_config)
    fpuset = sorted(fpu_config.keys())
    print("fpu_ids = %r" % fpuset)



    rd, grid_state = init_driver(args, max(fpuset), protected=False)
    

    if "test_can_connection" in args.tasks:
        print("[test_can_connection] ###")
        for fpu_id in fpuset:
            rv = check_can_connection(rd, args, fpu_id)

        

    if "flash_snum"    in args.tasks:
        print("[flash_snum] ###")
        for fpu_id in fpuset:
            serial_number = fpu_config[fpu_id]['serialnumber']
            
            
            print("flashing FPU #%i with serial number %r ... " % (fpu_id, serial_number), end='')
            flush()
            rval = rd.writeSerialNumber(fpu_id, serial_number, grid_state)
            print(rval)
            rd.readSerialNumbers(grid_state)

    env = None
    if "init_positions"    in args.tasks:
        print("[init_positions] ###")
        
        env = lmdb.open(DATABASE_FILE_NAME, max_dbs=10, map_size=dbsize)
        fpudb = env.open_db("fpu")
        
        for fpu_id in fpuset:
            alpha_start, beta_start = fpu_config[fpu_id]['pos']
            serialnumber = fpu_config[fpu_id]['serialnumber']
                                    
            init_position(env, fpudb, fpu_id, serialnumber,
                          alpha_start, beta_start, re_initialize=args.re_initialize)
            

    # switch to protected driver instance
    if len(set(args.tasks).intersection([ "test_datum",
                                          "test_alpha_max",
                                          "test_beta_max",
                                          "test_beta_min" ])) > 0:
        
        del rd # delete raw (unprotected) driver instance
        print("[initialize protected driver] ###")
        gd, grid_state = init_driver(args, max(fpuset), protected=True)
        
        
    if "test_datum" in args.tasks:
        print("[test_datum] ###")
        
        # We can use grid_state to display the starting position
        print("the starting position (in degrees) is:", gd.trackedAngles(grid_state))
        test_datum(gd, grid_state, args, fpuset)
        
    if "test_alpha_max" in args.tasks:
        pass

    if "test_beta_max" in args.tasks:
        pass

    if "test_beta_min" in args.tasks:
        pass
        
