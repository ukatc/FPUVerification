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
from vfr.conf import (ALPHA_DATUM_OFFSET, )

from vfr.tasks import *
import vfr.tasks as tsk

from vfr.posdb import init_position
from vfr.functional_tests import (test_datum, find_datum,  test_limit,
                                  DASEL_BOTH, DASEL_ALPHA, DASEL_BETA)

from vfr.connection import check_ping_ok, check_connection, check_can_connection, init_driver

    
 


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

    tasks = tsk.resolve(args.tasks)
    

    # check connections to cameras and EtherCAN gateway
        

    if TST_GATEWAY_CONNECTION in tasks:
        print("[%s] ###" % TST_GATEWAY_CONNECTION)
        check_connection(args, "gateway", args.gateway_address)

    if TST_POS_REP_CAM_CONNECTION in tasks:
        print("[%s] ###" % TST_POS_REP_CAM_CONNECTION)
        check_connection(args, "positional repetability camera", POS_REP_CAMERA_IP_ADDRESS)

    if TST_MET_CAL_CAM_CONNECTION in tasks:
        print("[%s] ###" % TST_MET_CAL_CAM_CONNECTION)
        check_connection(args, "metrology calibration camera", POS_REP_CAMERA_IP_ADDRESS)

    if TST_MET_HEIGHT_CAM_CONNECTION in tasks:
        print("[%s] ###" % TST_MET_HEIGHT_CAM_CONNECTION)
        check_connection(args, "metrology height camera", MET_HEIGHT_CAMERA_IP_ADDRESS)

    if TST_PUPIL_ALGN_CAM_CONNECTION in tasks:
        print("[%s] ###" % TST_PUPIL_ALGN_CAM_CONNECTION)
        check_connection(args, "pupil alignment camera", PUPIL_ALGN_CAMERA_IP_ADDRESS)

    fpu_config = load_config(args.setup_file)


    print("config= %r" % fpu_config)
    fpuset = sorted(fpu_config.keys())
    print("fpu_ids = %r" % fpuset)



    if TASK_INIT_RD:
        
        print("[initialize unprotected FPU driver] ###")

        rd, grid_state = init_driver(args, max(fpuset), protected=False)
    

    if TST_CAN_CONNECTION in tasks:
        print("[test_can_connection] ###")
        for fpu_id in fpuset:
            rv = check_can_connection(rd, grid_state, args, fpu_id)

        

    if TST_FLASH in tasks:
        print("[flash_snum] ###")
        for fpu_id in fpuset:
            serial_number = fpu_config[fpu_id]['serialnumber']
            
            
            print("flashing FPU #%i with serial number %r ... " % (fpu_id, serial_number), end='')
            flush()
            rval = rd.writeSerialNumber(fpu_id, serial_number, grid_state)
            print(rval)
            rd.readSerialNumbers(grid_state)

    fpudb = env.open_db("fpu")
    
    if TST_INITPOS    in tasks:
        print("[init_positions] ###")
        
        
        for fpu_id in fpuset:
            alpha_start, beta_start = fpu_config[fpu_id]['pos']
            serialnumber = fpu_config[fpu_id]['serialnumber']
                                    
            init_position(env, fpudb, fpu_id, serialnumber,
                          alpha_start, beta_start, re_initialize=args.re_initialize)
            

    vfdb = env.open_db("verification")

    # switch to protected driver instance, if needed
    
    if TASK_INIT_GD:

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

                     
            
    if TST_DATUM_ALPHA in tasks:
        print("[%s] ###" % TST_DATUM_ALPHA)
        
        # We can use grid_state to display the starting position
        print("the starting position (in degrees) is:", gd.trackedAngles(grid_state, retrieve=True))
        test_datum(env, vfdb, gd, grid_state, args, fpuset, fpu_config, DASEL_ALPHA)
        
    if TST_DATUM_BETA in tasks:
        print("[%s] ###" % TST_DATUM_BETA)
        
        # We can use grid_state to display the starting position
        print("the starting position (in degrees) is:", gd.trackedAngles(grid_state, retrieve=True))
        test_datum(env, vfdb, gd, grid_state, args, fpuset, fpu_config, DASEL_BETA)

    if TASK_REFERENCE in tasks:
        print("[%s] ###" % TASK_REFERENCE)
        # move all fpus to datum which are not there
        # (this is needed to operate the turntable)
        unreferenced = []
        for fpu_id, fpu in grid_state.FPUs:
            if fpu.state != FPST_AT_DATUM:
                unreferenced.append(fpu_id)

        if len(unreferenced) > 0 :
            gd.findDatum(grid_state, fpuset=unreferenced, timeout=DATUM_TIMEOUT_DISABLE)
        
        
    if TST_COLLDETECT in tasks:
        print("[test_collision_detection] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, args, fpuset, fpu_config, "beta_collision")

    if TST_ALPHA_MAX in tasks:
        print("[test_limit_alpha_max] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, args, fpuset, fpu_config, "alpha_max")

    
    if TST_ALPHA_MIN in tasks:
        print("[test_limit_alpha_min] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, args, fpuset, fpu_config, "alpha_min")


    if TST_BETA_MAX in tasks:
        print("[test_limit_beta_max] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, args, fpuset, fpu_config, "beta_max")


    if TST_BETA_MIN in tasks:
        print("[test_limit_beta_min] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, args, fpuset, fpu_config, "beta_min")
        
        
    if MEASURE_DATUM_REP in tasks:
        print("[%s] ###" % MEASURE_DATUM_REP)
        measure_datum_repeatability(env, vfdb, gd, grid_state, args, fpuset, fpu_config,
                                    **DATUM_REP_PARS)
    if EVAL_DATUM_REP in tasks:
        print("[%s] ###" % EVAL_DATUM_REP)
        eval_datum_repeatability(env, vfdb, gd, grid_state, args, fpuset, fpu_config,
                                 POSREP_ANALYSIS_PARS)
        
        
    if MEASURE_MET_CAL in tasks:
        print("[%s] ###" % MEASURE_MET_CAL)
        measure_metrology_calibration(env, vfdb, gd, grid_state, args, fpuset, fpu_config,
                                    **MET_CAL_PARS)
    if EVAL_MET_CAL in tasks:
        print("[%s] ###" % EVAL_MET_CAL)
        eval_metrology_calibration(env, vfdb, gd, grid_state, args, fpuset, fpu_config,
                                   METCAL_TARGET_ANALYSIS_PARS, METCAL_FIBRE_ANALYSIS_PARS)
        
        
        
