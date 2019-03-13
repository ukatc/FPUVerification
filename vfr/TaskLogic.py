from __future__ import print_function, division

from vfr.db.datum import get_datum_passed_p
from vfr.db.datum_repeatability import get_datum_repeatability_passed_p
from vfr.db.colldect_limits import get_colldect_passed_p
from vfr.db.pupil_alignment import get_pupil_alignment_passed_p
from vfr.db.positional_repeatability import get_positional_repeatability_passed_p

class T:
    # evaluation of measurements
    EVAL_DATUM_REP                 = "eval_datum_rep"
    EVAL_MET_CAL                   = "eval_met_cal"
    EVAL_MET_HEIGHT                = "eval_met_height"
    EVAL_POS_REP                   = "eval_pos_rep"
    EVAL_PUPIL_ALGN                = "eval_pup_align"
    # measurements
    MEASURE_ALL                    = "measure_all"
    MEASURE_DATUM_REP              = "measure_datum_rep"
    MEASURE_MET_CAL                = "measure_met_cal"
    MEASURE_MET_HEIGHT             = "measure_met_height"
    MEASURE_POS_REP                = "measure_pos_rep"
    MEASURE_PUPIL_ALGN             = "measure_pup_align"
    # conditional dependencies (can be skipped if done once)
    REQ_DATUM_PASSED               = "req_datum_passed"
    REQ_COLLDECT_PASSED            = "req_colldect_passed"
    REQ_DATUM_REP_PASSED           = "req_datum_repeatability_passed"
    REQ_FUNCTIONAL_PASSED          = "req_functional_test_passed"
    REQ_POS_REP_PASSED             = "req_positional_repeatability_passed"
    REQ_PUP_ALGN_PASSED            = "req_pupil_alignment_passed"
    # tasks which pack measurements and evaluation in pairs
    TASK_EVAL_ALL                  = "evaluate_all"
    TASK_INIT_GD                   = "initialize_grid_driver"
    TASK_INIT_RD                   = "initialize_unprotected_fpu_driver"
    TASK_MEASURE_ALL               = "measure_all"
    TASK_REFERENCE                 = "reference_step_counters"
    TASK_SELFTEST                  = "selftest"
    TASK_REPORT                    = "report"
    TASK_DUMP                      = "dump"
    # elementary tests
    TST_ALPHA_MAX                  = "test_alpha_max"
    TST_ALPHA_MIN                  = "test_alpha_min"
    TST_BETA_MAX                   = "test_beta_max"
    TST_BETA_MIN                   = "test_beta_min"
    TST_CAN_CONNECTION             = "test_can_connection"
    TST_COLLDETECT                 = "test_collision_detection"
    TST_DATUM                      = "test_datum"
    TST_DATUM_ALPHA                = "test_datum_alpha"
    TST_DATUM_BETA                 = "test_datum_beta"
    TST_DATUM_REP                  = "test_datum_repeatability"
    TST_FLASH                      = "flash"
    TST_FUNCTIONAL                 = "test_functional"
    TST_GATEWAY_CONNECTION         = "test_gateway_connection"
    TST_INIT                       = "init"
    TST_INITPOS                    = "init_positions"
    TST_LIMITS                     = "test_limits"
    TST_MET_CAL                    = "test_met_cal"
    TST_MET_CAL_CAM_CONNECTION     = "test_met_camera_connection"
    TST_MET_HEIGHT                 = "test_met_height"
    TST_MET_HEIGHT_CAM_CONNECTION  = "test_met_height_camera_connection"
    TST_POS_REP                    = "test_pos_rep"
    TST_POS_REP_CAM_CONNECTION     = "test_pos_reteatability_camera_connection"
    TST_POS_VER                    = "test_pos_ver"
    TST_PUPIL_ALGN                 = "test_pup_align"
    TST_PUPIL_ALGN_CAM_CONNECTION  = "test_pup_alignment_camera_connection"



usertasks = set([ T.EVAL_DATUM_REP               , 
                  T.EVAL_DATUM_REP               ,  
                  T.EVAL_MET_CAL                 , 
                  T.EVAL_MET_CAL                 ,  
                  T.EVAL_MET_HEIGHT              , 
                  T.EVAL_MET_HEIGHT              ,  
                  T.EVAL_POS_REP                 , 
                  T.EVAL_POS_REP                 ,  
                  T.EVAL_PUPIL_ALGN              ,
                  T.EVAL_PUPIL_ALGN              ,                    
                  T.MEASURE_DATUM_REP            , 
                  T.MEASURE_DATUM_REP            ,  
                  T.MEASURE_MET_CAL              , 
                  T.MEASURE_MET_CAL              ,  
                  T.MEASURE_MET_HEIGHT           ,  
                  T.MEASURE_MET_HEIGHT           ,                     
                  T.MEASURE_POS_REP              , 
                  T.MEASURE_POS_REP              ,  
                  T.MEASURE_PUPIL_ALGN           , 
                  T.MEASURE_PUPIL_ALGN           ,
                  T.TST_FLASH                    ,
                  T.TASK_DUMP                    ,
                  T.TASK_MEASURE_ALL             ,
                  T.TASK_REFERENCE               ,
                  T.TASK_REPORT                  ,
                  T.TASK_SELFTEST                ,
                  T.TST_ALPHA_MAX                , 
                  T.TST_ALPHA_MIN                , 
                  T.TST_BETA_MAX                 , 
                  T.TST_BETA_MIN                 , 
                  T.TST_CAN_CONNECTION           , 
                  T.TST_COLLDETECT               , 
                  T.TST_DATUM                    , 
                  T.TST_DATUM_ALPHA              , 
                  T.TST_DATUM_BETA               , 
                  T.TST_DATUM_REP                , 
                  T.TST_FLASH                    , 
                  T.TST_FUNCTIONAL               , 
                  T.TST_GATEWAY_CONNECTION       , 
                  T.TST_INIT                     , 
                  T.TST_INITPOS                  , 
                  T.TST_LIMITS                   , 
                  T.TST_MET_CAL                  , 
                  T.TST_MET_CAL_CAM_CONNECTION   , 
                  T.TST_MET_HEIGHT_CAM_CONNECTION, 
                  T.TST_POS_REP                  , 
                  T.TST_POS_REP_CAM_CONNECTION   , 
                  T.TST_POS_VER                  , 
                  T.TST_PUPIL_ALGN               , 
                  T.TST_PUPIL_ALGN_CAM_CONNECTION, 
                  T.TASK_EVAL_ALL    ,])


# task dependencies (where doing one task requires doing another task before)
task_dependencies = [ (T.TST_CAN_CONNECTION, [T.TST_GATEWAY_CONNECTION, T.TASK_INIT_RD]),
                      
                      (T.TST_FLASH, [T.TASK_INIT_RD, T.TST_CAN_CONNECTION]),
                      
                      (T.TST_INITPOS, []),
                      
                      (T.TST_DATUM_ALPHA, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION]),
                      
                      (T.TST_DATUM_BETA, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION]),
                      
                      (T.TST_ALPHA_MAX, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.REQ_DATUM_PASSED, T.TASK_REFERENCE]),
                      
                      (T.TST_ALPHA_MIN, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.REQ_DATUM_PASSED, T.TASK_REFERENCE]),
                      
                      (T.TST_BETA_MAX, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.REQ_DATUM_PASSED, T.TASK_REFERENCE]),
                      
                      (T.TST_BETA_MIN, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.REQ_DATUM_PASSED, T.TASK_REFERENCE]),

                      (T.TST_COLLDETECT, [T.REQ_DATUM_PASSED, T.TASK_REFERENCE ]),
                      
                      (T.MEASURE_DATUM_REP, [T.TASK_SELFTEST, T.TST_POS_REP_CAM_CONNECTION, T.REQ_DATUM_PASSED,
                                             T.REQ_COLLDECT_PASSED, T.TASK_REFERENCE]),
                      
                      (T.MEASURE_POS_REP, [T.TASK_SELFTEST, T.TST_POS_REP_CAM_CONNECTION, T.TASK_REFERENCE,
                                           T.REQ_DATUM_PASSED, T.REQ_COLLDECT_PASSED,
                                           # T.REQ_PUP_ALGN_PASSED,
                                           T.REQ_DATUM_REP_PASSED]),
                      
                      (T.TST_POS_VER, [T.TASK_SELFTEST, T.TST_POS_REP_CAM_CONNECTION,
                                       T.REQ_DATUM_PASSED, T.REQ_COLLDECT_PASSED,
                                       # T.REQ_PUP_ALGN_PASSED,
                                       T.REQ_DATUM_REP_PASSED,
                                       T.REQ_POS_REP_PASSED,
                                       T.TASK_REFERENCE]),
                      
                      (T.MEASURE_MET_CAL, [T.TASK_SELFTEST, T.TST_MET_CAL_CAM_CONNECTION]),
                      
                      (T.MEASURE_MET_HEIGHT, [T.TASK_SELFTEST, T.TST_MET_HEIGHT_CAM_CONNECTION]),
                      
                      (T.MEASURE_PUPIL_ALGN, [T.TASK_SELFTEST, T.TST_PUPIL_ALGN_CAM_CONNECTION,
                                              T.REQ_DATUM_PASSED, T.REQ_COLLDECT_PASSED, T.TASK_REFERENCE]),
                      
                      (T.MEASURE_ALL, [ T.TASK_SELFTEST                ,
                                        T.TST_GATEWAY_CONNECTION       , 
                                        T.TST_CAN_CONNECTION           , 
                                        T.TST_POS_REP_CAM_CONNECTION   , 
                                        T.TST_MET_CAL_CAM_CONNECTION   , 
                                        T.TST_MET_HEIGHT_CAM_CONNECTION, 
                                        T.TST_PUPIL_ALGN_CAM_CONNECTION, 
                                        T.TST_DATUM                    , 
                                        T.MEASURE_DATUM_REP            , 
                                        T.TST_MET_CAL                  , 
                                        T.MEASURE_MET_CAL              , 
                                        T.TST_POS_REP                  , 
                                        T.MEASURE_POS_REP              , 
                                        T.TST_POS_VER                  , 
                                        T.MEASURE_MET_HEIGHT           ,                     
                                        T.TST_PUPIL_ALGN               , 
                                        T.MEASURE_PUPIL_ALGN           ,    ]),
                      
                      (T.TASK_EVAL_ALL, [T.EVAL_DATUM_REP               , 
                                       T.EVAL_MET_CAL                 , 
                                       T.EVAL_POS_REP                 , 
                                       T.EVAL_MET_HEIGHT              , 
                                       T.EVAL_PUPIL_ALGN              ,    ]),

]

# conditional dependencies which are skipped if last test was already
# passed for all FPUs, otherwise the listed tasks are addded.
conditional_dependencies = [ (T.REQ_DATUM_REP_PASSED, get_datum_repeatability_passed_p, [T.TST_DATUM_REP, ]),
                             (T.REQ_DATUM_PASSED, get_datum_passed_p, [T.TST_DATUM]),
                             (T.REQ_COLLDECT_PASSED, get_colldect_passed_p, [T.TST_COLLDETECT]),
                             (T.REQ_PUP_ALGN_PASSED, get_pupil_alignment_passed_p, [T.TST_PUPIL_ALGN]),
                             (T.REQ_POS_REP_PASSED, get_positional_repeatability_passed_p, [T.TST_POS_REP]),
]


# task expansions (where one user-selectable task contains several sub-tasks)
task_expansions = [ (T.TST_INIT, [T.TST_FLASH,
                                  T.TST_INITPOS,]),
                    
                    (T.TST_DATUM, [T.TST_DATUM_ALPHA,
                                   T.TST_DATUM_BETA]),
                    
                    (T.TST_FUNCTIONAL, [T.TST_GATEWAY_CONNECTION,
                                        T.TST_CAN_CONNECTION,
                                        T.TST_DATUM,
                                        T.TST_ALPHA_MAX,
                                        T.TST_BETA_MAX,
                                        T.TST_BETA_MIN]),
                    
                    (T.TST_LIMITS, [T.TST_COLLDETECT,
                                    T.TST_ALPHA_MAX,
                                    T.TST_ALPHA_MIN,
                                    T.TST_BETA_MAX,
                                    T.TST_BETA_MIN]),
                    
                    (T.TST_DATUM_REP, [T.MEASURE_DATUM_REP,
                                       T.EVAL_DATUM_REP]),
                    
                    (T.TST_MET_CAL, [T.MEASURE_MET_CAL,
                                     T.EVAL_MET_CAL]),
                    
                    (T.TST_MET_HEIGHT, [T.MEASURE_MET_HEIGHT,
                                      T.EVAL_MET_HEIGHT]),                        
                    
                    (T.TST_POS_REP, [T.MEASURE_POS_REP,
                                     T.EVAL_POS_REP]),
                    
                    (T.TST_PUPIL_ALGN, [T.MEASURE_PUPIL_ALGN,
                                        T.EVAL_PUPIL_ALGN]),
                    
                    (T.TST_LIMITS, [T.TST_DATUM]),
                    (T.TST_ALPHA_MAX,[ T.TST_DATUM, ]),
                    (T.TST_ALPHA_MIN,[ T.TST_DATUM, ]),
                    (T.TST_BETA_MAX, [ T.TST_DATUM, ]),
                    (T.TST_BETA_MIN, [ T.TST_DATUM, ]),
]


def set_empty(set1):
    return len(set1) == 0


def all_true(testfun, sequence):
    passed = True
    for item in sequence:
        if not testfun(item):
            passed = False
            break

    return passed

def expand_tasks(tasks, goal, expansion, delete=False):
    if goal in tasks:
        print("[expanding %s to %r] ###" % (goal, expansion))
        
        if delete:
                      tasks.remove(goal)
                      tasks.update(expansion)

    return tasks
                      
def resolve(tasks, env, vfdb, opts, fpu_config, fpuset) :
    tasks = set(tasks)
                      
    for tsk in tasks:
        if tsk not in usertasks:
                      
            raise ValueError("invalid task name '%s'" % tsk)
                      
    while True:

        last_tasks = tasks.copy()
        # check for expansions (replace user shorthands by detailed task breakdown)
        for tsk, expansion in task_expansions:
                      tasks = expand_tasks(tasks, tsk, expansion, delete=True)

        # add dependencies (add tasks required to do a test)
        for tsk, expansion in task_dependencies:
                      tasks = expand_tasks(tasks, tsk, expansion)                      


        # add conditional dependencies (add tests which need to be passed before,
        # and are not already passed by all FPUs)
        for tsk, testfun, cond_expansion in conditional_dependencies:
            if tsk in tasks:
                tfun = lambda fpu_id: testfun(env, vfdb, opts, fpu_config, fpu_id)
                if (not all_true(tfun, fpuset)) or opts.repeat_passed_tests:
                    tasks = expand_tasks(tasks, tsk, cond_expansion, delete=True)
                    
        # check for equality with last iteration
        # -- if equal, expansion is finished
        if tasks == last_tasks:
            break
                      
    return tasks


