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
from vfr.conf import (DEFAULT_TASKS,
                      ALPHA_DATUM_OFFSET,
                      TST_GATEWAY_CONNECTION, 
                      TST_CAN_CONNECTION,     
                      TST_DATUM,              
                      TST_ALPHA_MIN,          
                      TST_ALPHA_MAX,
                      TST_BETA_MAX,           
                      TST_BETA_MIN,
                      TST_FUNCTIONAL,
                      TST_INIT,
                      TST_FLASH,
                      TST_INITPOS,
                      TST_LIMITS)

from vfr.posdb import init_position
from vfr.functional_tests import (test_datum, find_datum,  test_limit,
                                  DASEL_BOTH, DASEL_ALPHA, DASEL_BETA)

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
        if tsk not in [TST_GATEWAY_CONNECTION,
                       TST_CAN_CONNECTION,
                       TST_DATUM,
                       TST_FUNCTIONAL,
                       TST_FLASH,
                       TST_INIT,
                       TST_INITPOS,
                       TST_LIMITS,
                       TST_ALPHA_MAX,
                       TST_ALPHA_MIN,
                       TST_BETA_MAX,
                       TST_BETA_MIN, ]:
            
            raise ValueError("invalid task name '%s'" % tsk)
        
    
    if TST_INIT in args.tasks:
        expansion = [TST_FLASH,
                     TST_INITPOS,]
        
        print("[expanding init] ###")
        print("...expanded to %r" % expansion)
        args.tasks.extend(expansion)
        
    if TST_FUNCTIONAL in args.tasks:
        expansion = [TST_GATEWAY_CONNECTION,
                     TST_CAN_CONNECTION,
                     TST_DATUM,
                     TST_ALPHA_MAX,
                     TST_BETA_MAX,
                     TST_BETA_MIN]
        
        print("[expanding test_functional] ###")
        print("...expanded to %r" % expansion)
        args.tasks.extend(expansion)

    if TST_GATEWAY_CONNECTION in args.tasks:
        print("[test_gateway_connection] ###")
        check_gateway_connection(args)

    fpu_config = load_config(args.setup_file)


    print("config= %r" % fpu_config)
    fpuset = sorted(fpu_config.keys())
    print("fpu_ids = %r" % fpuset)


    tasks_which_need_rd = [ TST_CAN_CONNECTION,
                            TST_FLASH, ]

    if not set_empty(intersection(set(args.tasks),
                                  set(tasks_which_need_rd))):
        
        print("[initialize unprotected FPU driver] ###")

        rd, grid_state = init_driver(args, max(fpuset), protected=False)
    

    if TST_CAN_CONNECTION in args.tasks:
        print("[test_can_connection] ###")
        for fpu_id in fpuset:
            rv = check_can_connection(rd, grid_state, args, fpu_id)

        

    if TST_FLASH in args.tasks:
        print("[flash_snum] ###")
        for fpu_id in fpuset:
            serial_number = fpu_config[fpu_id]['serialnumber']
            
            
            print("flashing FPU #%i with serial number %r ... " % (fpu_id, serial_number), end='')
            flush()
            rval = rd.writeSerialNumber(fpu_id, serial_number, grid_state)
            print(rval)
            rd.readSerialNumbers(grid_state)

    if TST_INITPOS    in args.tasks:
        print("[init_positions] ###")
        
        fpudb = env.open_db("fpu")
        
        for fpu_id in fpuset:
            alpha_start, beta_start = fpu_config[fpu_id]['pos']
            serialnumber = fpu_config[fpu_id]['serialnumber']
                                    
            init_position(env, fpudb, fpu_id, serialnumber,
                          alpha_start, beta_start, re_initialize=args.re_initialize)
            

    vfdb = env.open_db("verification")

    # switch to protected driver instance, if needed
    tasks_which_need_gd = [ TST_DATUM,
                            TST_ALPHA_MAX,
                            TST_BETA_MAX,
                            TST_BETA_MIN ]
    
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

    if not set_empty(intersection(set(args.tasks), set([TST_LIMITS,
                                                        TST_ALPHA_MAX,
                                                        TST_ALPHA_MIN,
                                                        TST_BETA_MAX,
                                                        TST_BETA_MIN]))):
        args.tasks.append(test_datum)
                     
    
    if TST_DATUM in args.tasks:
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
        
    if TST_LIMITS in args.tasks:
        expansion = [TST_ALPHA_MAX,
                     TST_ALPHA_MIN,
                     TST_BETA_MAX,
                     TST_BETA_MIN]
        
        print("[expanding test_limits] ###")
        print("...expanded to %r" % expansion)
        args.tasks.extend(expansion)
        
    if TST_ALPHA_MAX in args.tasks:
        print("[test_limit_alpha_max] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, args, fpuset, fpu_config, "alpha_max")

    
    if TST_ALPHA_MIN in args.tasks:
        print("[test_limit_alpha_min] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, args, fpuset, fpu_config, "alpha_min")


    if TST_BETA_MAX in args.tasks:
        print("[test_limit_beta_max] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, args, fpuset, fpu_config, "beta_max")


    if TST_BETA_MIN in args.tasks:
        print("[test_limit_beta_min] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, args, fpuset, fpu_config, "beta_min")
        
