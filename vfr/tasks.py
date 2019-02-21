from __future__ import print_function, division

EVAL_DATUM_REP                 = "eval_datum_repeatability"
EVAL_MET_CAL                   = "ecval_metrology_calibration"
EVAL_MET_HEIGHT                = "eval_metrology_target_height"
EVAL_POS_REP                   = "eval_positional_repeatability"
EVAL_PUPIL_ALGN                = "eval_pupil_alignment"
MEASURE_DATUM_REP              = "measure_datum_repeatability"
MEASURE_MET_CAL                = "measure_metrology_calibration"
MEASURE_MET_HEIGHT             = "measure_metrology_target_height"
MEASURE_POS_REP                = "measure_positional_repeatability"
MEASURE_PUPIL_ALGN             = "measure_pupil_alignment"
TASK_INIT_GD                   = "initialize_grid_driver"
TASK_INIT_RD                   = "initialize_unprotected_fpu_driver"
TASK_REFERENCE                 = "reference_FPU_step_counters"
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
TST_FLASH                      = "flash_snum"
TST_FUNCTIONAL                 = "test_functional"
TST_GATEWAY_CONNECTION         = "test_gateway_connection"
TST_INIT                       = "init"
TST_INITPOS                    = "init_positions"
TST_LIMITS                     = "test_limits"
TST_MET_CAL                    = "test_metrology_calibration"
TST_MET_CAL_CAM_CONNECTION     = "test_metrology_camera_connection"
TST_MET_HEIGHT_CAM_CONNECTION  = "test_metrology_height_camera_connection"
TST_POS_REP                    = "test_positional_repeatability"
TST_POS_REP_CAM_CONNECTION     = "test_positional_repetability_camera_connection"
TST_POS_VER                    = "test_positional_verification"
TST_PUPIL_ALGN                 = "test_pupil_alignment"
TST_PUPIL_ALGN_CAM_CONNECTION  = "test_pupil_alignment_camera__connection"


DEFAULT_TASKS = [TST_GATEWAY_CONNECTION,
                 TST_CAN_CONNECTION,
                 TST_FLASH,
                 TST_INITPOS,
                 TST_DATUM,
                 TST_CDECT,
                 TST_ALPHA_MAX,
                 TST_BETA_MAX,
                 TST_BETA_MIN,
                 TST_DATUM_REP,
                 TST_MET_CAL]

usertasks = set([TST_GATEWAY_CONNECTION       , 
                 TST_CAN_CONNECTION           , 
                 TST_POS_REP_CAM_CONNECTION   , 
                 TST_MET_CAL_CAM_CONNECTION   , 
                 TST_MET_HEIGHT_CAM_CONNECTION, 
                 TST_PUPIL_ALGN_CAM_CONNECTION, 
                 TST_DATUM                    , 
                 TST_DATUM_ALPHA              , 
                 TST_DATUM_BETA               , 
                 TST_COLLDETECT               , 
                 TST_ALPHA_MIN                , 
                 TST_ALPHA_MAX                , 
                 TST_BETA_MAX                 , 
                 TST_BETA_MIN                 , 
                 TST_FUNCTIONAL               , 
                 TST_INIT                     , 
                 TST_FLASH                    , 
                 TST_INITPOS                  , 
                 TST_LIMITS                   , 
                 TST_DATUM_REP                , 
                 MEASURE_DATUM_REP            , 
                 EVAL_DATUM_REP               , 
                 TST_MET_CAL                  , 
                 MEASURE_MET_CAL              , 
                 EVAL_MET_CAL                 , 
                 TST_POS_REP                  , 
                 MEASURE_POS_REP              , 
                 EVAL_POS_REP                 , 
                 TST_POS_VER                  , 
                 MEASURE_MET_HEIGHT           ,                     
                 EVAL_MET_HEIGHT              , 
                 TST_PUPIL_ALGN               , 
                 MEASURE_PUPIL_ALGN           , 
                 EVAL_PUPIL_ALGN              ,    ])





        

   

    
    

# task dependencies (where doing one task requires doing another task before)
task_dependencies = [ (TST_CAN_CONNECTION, [TST_GATEWAY_CONNECTION, TASK_INIT_RD]),
                      (TST_FLASH, [TASK_INIT_RD, TST_CAN_CONNECTION]),
                      (TST_INITPOS, []),
                      (TST_DATUM_ALPHA, [TASK_INIT_GD, TST_CAN_CONNECTION]),
                      (TST_DATUM_BETA, [TASK_INIT_GD, TST_CAN_CONNECTION]),
                      (TST_ALPHA_MAX, [TASK_INIT_GD, TST_CAN_CONNECTION, TASK_REFERENCE]),
                      (TST_ALPHA_MIN, [TASK_INIT_GD, TST_CAN_CONNECTION, TASK_REFERENCE]),
                      (TST_BETA_MAX, [TASK_INIT_GD, TST_CAN_CONNECTION, TASK_REFERENCE]),
                      (TST_BETA_MIN, [TASK_INIT_GD, TST_CAN_CONNECTION, TASK_REFERENCE]),
                      (MEASURE_DATUM_REP, [TST_POS_REP_CAM_CONNECTION, TASK_REFERENCE]),
                      (MEASURE_POS_REP, [TST_POS_REP_CAM_CONNECTION, TASK_REFERENCE]),
                      (TST_POS_VER, [TST_POS_REP_CAM_CONNECTION, TASK_REFERENCE]),
                      (MEASURE_MET_CAL, [TST_MET_CAL_CAM_CONNECTION, TASK_REFERENCE]),
                      (MEASURE_MET_HEIGHT, [TST_MET_HEIGHT_CAM_CONNECTION, TASK_REFERENCE]),
                      (MEASURE_PUPIL_ALGN, [TST_PUPIL_ALGN_CAM_CONNECTION, TASK_REFERENCE]),


# task expansions (where one user-selectable task contains several sub-tasks)
task_expansions = [ (TST_INIT, [TST_FLASH,
                                TST_INITPOS,]),
                    
                    (TST_DATUM, [TST_DATUM_ALPHA,
                                 TST_DATUM_BETA]),
                    
                    (TST_FUNCTIONAL, [TST_GATEWAY_CONNECTION,
                                      TST_CAN_CONNECTION,
                                      TST_DATUM,
                                      TST_ALPHA_MAX,
                                      TST_BETA_MAX,
                                      TST_BETA_MIN]),
                    
                    (TST_LIMITS, [TST_COLLDETECT,
                                  TST_ALPHA_MAX,
                                  TST_ALPHA_MIN,
                                  TST_BETA_MAX,
                                  TST_BETA_MIN]),
                    
                    (TST_DATUM_REP, [MEASURE_DATUM_REP,
                                     EVAL_DATUM_REP]),
                    
                    (TST_MET_CAL, [MEASURE_MET_CAL,
                                   EVAL_MET_CAL]),
                    
                    (TST_MET_HEIGHT, [MEASURE_MET_HEIGHT,
                                      EVAL_MET_HEIGHT]),                        
                    
                    (TST_POS_REP, [MEASURE_POS_REP,
                                   EVAL_POS_REP]),
                    
                    (TST_PUPIL_ALGN, [MEASURE_PUPIL_ALGN,
                                      EVAL_PUPIL_ALGN]),
                    
                    (TST_LIMITS, [TST_DATUM]),
                    (TST_ALPHA_MAX,[ TST_DATUM, ]),
                    (TST_ALPHA_MIN,[ TST_DATUM, ]),
                    (TST_BETA_MAX, [ TST_DATUM, ]),
                    (TST_BETA_MIN, [ TST_DATUM, ]),
]



def expand_tasks(goal, tasks, expansion, delete=False)
    if goal in tasks:
                      print("[expanding %s to %r] ###" % (goal, expansion))
        if delete:
                      tasks.remove(goal)
                      tasks.update(expansion)

    return tasks
                      
def resolve(tasks)    
                      tasks = set(tasks)
                      
    for tsk in tasks:
        if tsk not in usertasks:
                      
            raise ValueError("invalid task name '%s'" % tsk)
                      
    while True:

        n = len(tasks)
        for tsk, expansion in task_dependencies:
                      tasks = expand_tasks(tasks, tsk, expansion)
                      
        for tsk, expansion in task_expansions:
                      tasks = expand_tasks(tasks, tsk, expansion, delete=True)

        if n == len(tasks):
            break
                      
    return tasks


