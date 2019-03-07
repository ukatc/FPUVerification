#!/usr/bin/env python

from __future__ import print_function, division

import sys
import re
import os
import ast

from fpu_constants import *


from vfr.tests_common import flush

from vfr.db import env
from vfr.options import parse_args
from vfr.conf import (ALPHA_DATUM_OFFSET, )

from vfr.TaskLogic import T, resolve

from vfr.connection import check_ping_ok, check_connection, check_can_connection, init_driver

from vfr.posdb import init_position
from vfr.functional_tests import (test_datum, find_datum,  test_limit,
                                  DASEL_BOTH, DASEL_ALPHA, DASEL_BETA)

from vfr.verification_tasks.metrology_calibration import measure_metrology_calibration, eval_metrology_calibration

from vfr.verification_tasks.measure_datum_repeatability import measure_datum_repeatability, eval_datum_repeatability

from vfr.verification_tasks.positional_repeatability import measure_positional_repeatability, eval_positional_repeatability

from vfr.verification_tasks.metrology_height import measure_metrology_height, eval_metrology_height

    
 
sn_pat = re.compile('[a-zA-Z0-9]{1,5}$')


def load_config(config_file_name):
    print("reading configuratiom from %r..." % config_file_name)
    cfg_list = ast.literal_eval(''.join(open(config_file_name).readlines()))

    fconfig = dict([ (entry['fpu_id'], { 'serialnumber' : entry['serialnumber'],
                                     'pos' : entry['pos'],
                                     'fpu_id' : entry['fpu_id']}) for entry in cfg_list])

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


def get_sets(vfdb, fpu_config, opts):
    """Under normal operation, we want to measure and evaluate the FPUs
    in the rig.

    However, we also need to be able to query and/or re-evaluate data
    for FPUs which have been measured before. To do that, there is a
    command line parameter so that we can select a subset of all
    stored FPUs to be displayed.

    This allows also to restrict a new measurement to FPUs which are 
    explicityly listed, for example because the need to be selectively 
    repeated.

    """
    eval_snset = opts.snset
    
    
    if eval_snset == "all":
        # get the serial numbers of all FPUs which have been measured so far
        eval_snset = get_snset(env, vfdb)
    elif eval_snset is not None:
        # in this case, it needs to be a list of serial numbers
        eval_snset = set(eval_snset)

    # check passed serial numbers for validity
    for sn in eval_snset:
        if not sn_pat.match(sn):
            raise ValueError("serial number %r is not valid!" % sn)
        
    if eval_snset is None:
        # both mesured and evaluated sets are exclusively defined by
        # the measurement configuration file
        measure_fpuset = fpu_config.keys()
        eval_fpuset = fpuset
    else:
        # we restrict the measured FPUs to the serial numbers passed
        # in the command line option, and create a config which has
        # entries for these and the additional requested serial
        # numbers
        config_by_sn = {val['serialnumber'] : val for val in fpu_config.values()}
            
        config_sns = set(config_by_sn.keys())
        if len(config_sns) != len(fpu_config):
            raise ValueError("the measurement configuration file has duplicate serial numbers")
        
        measure_sns = config_sns.intersection(eval_snset)
        
        measure_config = {config_by_sn[sn]['fpu_id'] : config_by_sn[sn] for sn in measure_sns }
        
        measure_fpuset = fpu_config.keys()
        
        extra_eval_sns = requested_snset.difference(measure_sns)

        # we use the serial numbers as key - these need not to have
        # integer type as they are not used in measurements.
        
        fpu_config = { sn : {'serialnumber' : sn} for sn in extra_eval_sns}
        
        fpu_config.update(measure_config)

        eval_fpuset = fpu_config.keys()
                       
            
    return fpu_config, sorted(measure_fpuset), sorted(eval_fpuset)


if __name__ == '__main__':
    print("starting verification")
    opts = parse_args()
    print("tasks = %r" % opts.tasks)

    vfdb = env.open_db("verification")
    
    fpu_config = load_config(opts.setup_file)


    print("measurement config= %r" % fpu_config)


    # get sets of measured and evaluated FPUs
    fpu_config, measure_fpuset, eval_fpuset = get_sets(vfdb, fpu_config, opts)
    
    print("fpu_ids = %r" % measure_fpuset)


    # resolve high-level tasks and dependent checks and measurements into
    # low-level actions
    tasks = resolve(opts.tasks, env, vfdb, opts, fpu_config, measure_fpuset)

    # change current directory to image root
    os.chdir(IMAGE_ROOT_FOLDER)
    # check connections to cameras and EtherCAN gateway    

    if T.TST_GATEWAY_CONNECTION in tasks:
        print("[%s] ###" % T.TST_GATEWAY_CONNECTION)
        check_connection(opts, "gateway", opts.gateway_address)

    if T.TST_POS_REP_CAM_CONNECTION in tasks:
        print("[%s] ###" % T.TST_POS_REP_CAM_CONNECTION)
        check_connection(opts, "positional repetability camera", POS_REP_CAMERA_IP_ADDRESS)

    if T.TST_MET_CAL_CAM_CONNECTION in tasks:
        print("[%s] ###" % T.TST_MET_CAL_CAM_CONNECTION)
        check_connection(opts, "metrology calibration camera", POS_REP_CAMERA_IP_ADDRESS)

    if T.TST_MET_HEIGHT_CAM_CONNECTION in tasks:
        print("[%s] ###" % T.TST_MET_HEIGHT_CAM_CONNECTION)
        check_connection(opts, "metrology height camera", MET_HEIGHT_CAMERA_IP_ADDRESS)

    if T.TST_PUPIL_ALGN_CAM_CONNECTION in tasks:
        print("[%s] ###" % T.TST_PUPIL_ALGN_CAM_CONNECTION)
        check_connection(opts, "pupil alignment camera", PUPIL_ALGN_CAMERA_IP_ADDRESS)



    if T.TASK_INIT_RD:
        
        print("[initialize unprotected FPU driver] ###")

        rd, grid_state = init_driver(opts, max(measure_fpuset), protected=False)
    

    if T.TST_CAN_CONNECTION in tasks:
        print("[test_can_connection] ###")
        for fpu_id in measure_fpuset:
            rv = check_can_connection(rd, grid_state, opts, fpu_id)

        

    if T.TST_FLASH in tasks:
        print("[flash_snum] ###")
        for fpu_id in measure_fpuset:
            serial_number = fpu_config[fpu_id]['serialnumber']
            
            
            print("flashing FPU #%i with serial number %r ... " % (fpu_id, serial_number), end='')
            flush()
            rval = rd.writeSerialNumber(fpu_id, serial_number, grid_state)
            print(rval)
            rd.readSerialNumbers(grid_state)

    fpudb = env.open_db("fpu")
    
    if T.TST_INITPOS    in tasks:
        print("[init_positions] ###")
        
        
        for fpu_id in measure_fpuset:
            alpha_start, beta_start = fpu_config[fpu_id]['pos']
            serialnumber = fpu_config[fpu_id]['serialnumber']
                                    
            init_position(env, fpudb, fpu_id, serialnumber,
                          alpha_start, beta_start, re_initialize=opts.re_initialize)
            


    # switch to protected driver instance, if needed
    
    if T.TASK_INIT_GD:

        if locals().has_key('rd'):
            del rd # delete raw (unprotected) driver instance
            
        print("[initialize protected driver] ###")
        gd, grid_state = init_driver(opts, max(measure_fpuset), protected=True)

        gd.readSerialNumbers(grid_state)
        for fpu_id in measure_fpuset:
            actual_sn = grid_state.FPU[fpu_id].serial_number
            configured_sn = fpu_config[fpu_id]['serialnumber']
            if configured_sn != actual_sn:
                raise ValueError("actual serial number of FPU %i = %r does not match configuration (%r)" %
                                 (fpu_id, actual_sn, configured_sn))
        
    if opts.resetFPUs:
        print("resetting FPUs.... ", end='')
        flush()
        gd.resetFPUs(grid_state, fpuset=measure_fpuset)
        print("OK")

                     
            
    if T.TST_DATUM_ALPHA in tasks:
        print("[%s] ###" % T.TST_DATUM_ALPHA)
        
        # We can use grid_state to display the starting position
        print("the starting position (in degrees) is:", gd.trackedAngles(grid_state, retrieve=True))
        test_datum(env, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config, DASEL_ALPHA)
        
    if T.TST_DATUM_BETA in tasks:
        print("[%s] ###" % T.TST_DATUM_BETA)
        
        # We can use grid_state to display the starting position
        print("the starting position (in degrees) is:", gd.trackedAngles(grid_state, retrieve=True))
        test_datum(env, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config, DASEL_BETA)

    if T.TASK_REFERENCE in tasks:
        print("[%s] ###" % T.TASK_REFERENCE)
        # move all fpus to datum which are not there
        # (this is needed to operate the turntable)
        unreferenced = []
        for fpu_id, fpu in grid_state.FPUs:
            if fpu.state != FPST_AT_DATUM:
                unreferenced.append(fpu_id)

        if len(unreferenced) > 0 :
            gd.findDatum(grid_state, fpuset=unreferenced, timeout=DATUM_TIMEOUT_DISABLE)
        
        
    if T.TST_COLLDETECT in tasks:
        print("[test_collision_detection] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config, "beta_collision")

    if T.TST_ALPHA_MAX in tasks:
        print("[test_limit_alpha_max] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config, "alpha_max")

    
    if T.TST_ALPHA_MIN in tasks:
        print("[test_limit_alpha_min] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config, "alpha_min")


    if T.TST_BETA_MAX in tasks:
        print("[test_limit_beta_max] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config, "beta_max")


    if T.TST_BETA_MIN in tasks:
        print("[test_limit_beta_min] ###")
        test_limit(env, fpudb, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config, "beta_min")

        
    if T.MEASURE_MET_CAL in tasks:
        print("[%s] ###" % T.MEASURE_MET_CAL)
        measure_metrology_calibration(env, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config,
                                    **MET_CAL_PARS)
    if T.EVAL_MET_CAL in tasks:
        print("[%s] ###" % T.EVAL_MET_CAL)
        eval_metrology_calibration(env, vfdb, gd, grid_state, opts, eval_fpuset, fpu_config,
                                   METCAL_TARGET_ANALYSIS_PARS, METCAL_FIBRE_ANALYSIS_PARS)

    if T.MEASURE_MET_HEIGHT in tasks:
        print("[%s] ###" % T.MEASURE_MET_HEIGHT)
        measure_metrology_height(env, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config,
                                 **MET_HEIGHT_ANALYSIS_PARS)
    if T.EVAL_MET_HEIGHT in tasks:
        print("[%s] ###" % T.EVAL_MET_HEIGHT)
        eval_metrology_height(env, vfdb, gd, grid_state, opts, eval_fpuset, fpu_config,
                              MET_HEIGHT_ANALYSIS_PARS, MET_HEIGHT_EVALUATION_PARS)

        
    if T.MEASURE_DATUM_REP in tasks:
        print("[%s] ###" % T.MEASURE_DATUM_REP)
        measure_datum_repeatability(env, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config,
                                    **DATUM_REP_PARS)
    if T.EVAL_DATUM_REP in tasks:
        print("[%s] ###" % T.EVAL_DATUM_REP)
        eval_datum_repeatability(env, vfdb, gd, grid_state, opts, eval_fpuset, fpu_config,
                                 POSREP_ANALYSIS_PARS)

    if T.MEASURE_PUPIL_ALGN in tasks:
        print("[%s] ###" % T.MEASURE_PUPIL_ALGN)
        measure_pupil_alignment(env, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config,
                                **PUPALGN_MEASUREMENT_PARS)
    if T.EVAL_PUPIL_ALGN in tasks:
        print("[%s] ###" % T.EVAL_PUPIL_ALGN)
        eval_pupil_alignment(env, vfdb, gd, grid_state, opts, eval_fpuset, fpu_config,
                             PUPALGN_CALIBRATION_PARS=PUPALGN_CALIBRATION_PARS,
                             PUPALGN_ANALYSIS_PARS=PUPALGN_ANALYSIS_PARS,
                             PUPALGN_EVALUATION_PARS)
        

    if T.MEASURE_POS_REP in tasks:
        print("[%s] ###" % T.MEASURE_POS_REP)
        measure_positional_repeatability(env, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config,
                                         **POSREP_MEASUREMENT_PARS)
        
    if T.EVAL_POS_REP in tasks:
        print("[%s] ###" % T.EVAL_POS_REP)
        eval_positional_repeatability(env, vfdb, gd, grid_state, opts, eval_fpuset, fpu_config,
                                      POSREP_CALIBRATION_PARS,
                                      POSREP_ANALYSIS_PARS,
                                      POSREP_EVALUATION_PARS)
        
    if T.MEASURE_POS_VER in tasks:
        print("[%s] ###" % T.MEASURE_POS_VER)
        measure_positional_verification(env, vfdb, gd, grid_state, opts, measure_fpuset, fpu_config,
                                        **POSVER_MEASUREMENT_PARS)
        
    if T.EVAL_POS_VER in tasks:
        print("[%s] ###" % T.EVAL_POS_VER)
        eval_positional_verification(env, vfdb, gd, grid_state, opts, eval_fpuset, fpu_config,
                                     POSREP_CALIBRATION_PARS,
                                     POSVER_ANALYSIS_PARS,
                                     POSVER_EVALUATION_PARS)
        
                
        
        
