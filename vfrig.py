#!/usr/bin/env python

from __future__ import print_function, division

import sys
import re
import os
import ast

from fpu_constants import *


from vfr.tests_common import flush

from vfr.db import env
from vfr.opts import parse_args
from vfr.conf import DEFAULT_TASKS, ALPHA_DATUM_OFFSET
from vfr.posdb import init_position
from vfr.functional_tests import test_datum, find_datum, rewind_fpus, DASEL_BOTH, DASEL_ALPHA, DASEL_BETA
from vfr.connection import check_ping_ok, check_gateway_connection, check_can_connection, init_driver

    
 


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


# two functional short-hands for set operations
def intersection(set1, set2):
    return set1.intersection(set2)

def set_empty(set1):
    return len(set1) == 0



    
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


    tasks_which_need_rd = [ "test_can_connection",
                            "flash_snum", ]

    if not set_empty(intersection(set(args.tasks),
                                  set(tasks_which_need_rd))):
        
        print("[initialize unprotected FPU driver] ###")

        rd, grid_state = init_driver(args, max(fpuset), protected=False)
    

    if "test_can_connection" in args.tasks:
        print("[test_can_connection] ###")
        for fpu_id in fpuset:
            rv = check_can_connection(rd, args, fpu_id)

        

    if "flash_snum" in args.tasks:
        print("[flash_snum] ###")
        for fpu_id in fpuset:
            serial_number = fpu_config[fpu_id]['serialnumber']
            
            
            print("flashing FPU #%i with serial number %r ... " % (fpu_id, serial_number), end='')
            flush()
            rval = rd.writeSerialNumber(fpu_id, serial_number, grid_state)
            print(rval)
            rd.readSerialNumbers(grid_state)

    if "init_positions"    in args.tasks:
        print("[init_positions] ###")
        
        fpudb = env.open_db("fpu")
        
        for fpu_id in fpuset:
            alpha_start, beta_start = fpu_config[fpu_id]['pos']
            serialnumber = fpu_config[fpu_id]['serialnumber']
                                    
            init_position(env, fpudb, fpu_id, serialnumber,
                          alpha_start, beta_start, re_initialize=args.re_initialize)
            

    vfdb = env.open_db("verification")

    # switch to protected driver instance, if needed
    tasks_which_need_gd = [ "test_datum",
                            "test_alpha_max",
                            "test_beta_max",
                            "test_beta_min" ]
    
    if not set_empty(intersection(set(args.tasks),
                                  set(tasks_which_need_gd))):

        if locals().has_key('rd'):
            del rd # delete raw (unprotected) driver instance
            
        print("[initialize protected driver] ###")
        gd, grid_state = init_driver(args, max(fpuset), protected=True)

        gd.readSerialNumbers(grid_state)
        for fpu_id in fpuset:
            actual_sn = grid_state.FPU[fpu_id].serial_number
            configured_sn = fpu_config[fpu_id]['serialnumber']
            if configured_sn != actual_sn:
                raise ValueError("actual serial number of FPU %i = %r does not match configuration (%r)" %
                                 (fpu_id, actual_sn, configured_sn))
        
    if args.resetFPUs:
        print("resetting FPUs.... ", end='')
        flush()
        gd.resetFPUs(grid_state, fpuset=fpuset)
        print("OK")
        
    if "test_datum" in args.tasks:
        expansion = ["test_datum_alpha",
                     "test_datum_beta",]
        
        print("[expanding test_datum] ###")
        print("...expanded to %r" % expansion)
        args.tasks.extend(expansion)
        
    if "test_datum_alpha" in args.tasks:
        print("[test_datum_alpha] ###")
        
        # We can use grid_state to display the starting position
        print("the starting position (in degrees) is:", gd.trackedAngles(grid_state, retrieve=True))
        test_datum(env, vfdb, gd, grid_state, args, fpuset, fpu_config, DASEL_ALPHA)
        
    if "test_datum_beta" in args.tasks:
        print("[test_datum_beta] ###")
        
        # We can use grid_state to display the starting position
        print("the starting position (in degrees) is:", gd.trackedAngles(grid_state, retrieve=True))
        test_datum(env, vfdb, gd, grid_state, args, fpuset, fpu_config, DASEL_BETA)
        
    if "test_alpha_max" in args.tasks:
        pass

    if "test_beta_max" in args.tasks:
        pass

    if "test_beta_min" in args.tasks:
        pass
        
