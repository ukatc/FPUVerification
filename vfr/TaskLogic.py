from __future__ import print_function, division

class T:
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
    TASK_MEASURE_ALL               = "measure_FPUs"
    TASK_EVAL_ALL                  = "evaluate"


DEFAULT_TASKS = [T.TST_GATEWAY_CONNECTION,
                 T.TST_CAN_CONNECTION,
                 T.TST_FLASH,
                 T.TST_INITPOS,
                 T.TST_DATUM,
                 T.TST_CDECT,
                 T.TST_ALPHA_MAX,
                 T.TST_BETA_MAX,
                 T.TST_BETA_MIN,
                 T.TST_DATUM_REP,
                 T.TST_MET_CAL]

usertasks = set([T.TST_GATEWAY_CONNECTION       , 
                 T.TST_CAN_CONNECTION           , 
                 T.TST_POS_REP_CAM_CONNECTION   , 
                 T.TST_MET_CAL_CAM_CONNECTION   , 
                 T.TST_MET_HEIGHT_CAM_CONNECTION, 
                 T.TST_PUPIL_ALGN_CAM_CONNECTION, 
                 T.TST_DATUM                    , 
                 T.TST_DATUM_ALPHA              , 
                 T.TST_DATUM_BETA               , 
                 T.TST_COLLDETECT               , 
                 T.TST_ALPHA_MIN                , 
                 T.TST_ALPHA_MAX                , 
                 T.TST_BETA_MAX                 , 
                 T.TST_BETA_MIN                 , 
                 T.TST_FUNCTIONAL               , 
                 T.TST_INIT                     , 
                 T.TST_FLASH                    , 
                 T.TST_INITPOS                  , 
                 T.TST_LIMITS                   , 
                 T.TST_DATUM_REP                , 
                 T.MEASURE_DATUM_REP            , 
                 T.EVAL_DATUM_REP               , 
                 T.TST_MET_CAL                  , 
                 T.MEASURE_MET_CAL              , 
                 T.EVAL_MET_CAL                 , 
                 T.TST_POS_REP                  , 
                 T.MEASURE_POS_REP              , 
                 T.EVAL_POS_REP                 , 
                 T.TST_POS_VER                  , 
                 T.MEASURE_MET_HEIGHT           ,                     
                 T.EVAL_MET_HEIGHT              , 
                 T.TST_PUPIL_ALGN               , 
                 T.MEASURE_PUPIL_ALGN           , 
                 T.EVAL_PUPIL_ALGN              ,    ])


# task dependencies (where doing one task requires doing another task before)
task_dependencies = [ (T.TST_CAN_CONNECTION, [T.TST_GATEWAY_CONNECTION, T.TASK_INIT_RD]),
                      
                      (T.TST_FLASH, [T.TASK_INIT_RD, T.TST_CAN_CONNECTION]),
                      
                      (T.TST_INITPOS, []),
                      
                      (T.TST_DATUM_ALPHA, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION]),
                      
                      (T.TST_DATUM_BETA, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION]),
                      
                      (T.TST_ALPHA_MAX, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.TASK_REFERENCE]),
                      
                      (T.TST_ALPHA_MIN, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.TASK_REFERENCE]),
                      
                      (T.TST_BETA_MAX, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.TASK_REFERENCE]),
                      
                      (T.TST_BETA_MIN, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.TASK_REFERENCE]),
                      
                      (T.MEASURE_DATUM_REP, [T.TST_POS_REP_CAM_CONNECTION, T.TASK_REFERENCE]),
                      
                      (T.MEASURE_POS_REP, [T.TST_POS_REP_CAM_CONNECTION, T.TASK_REFERENCE]),
                      
                      (T.TST_POS_VER, [T.TST_POS_REP_CAM_CONNECTION, T.TASK_REFERENCE]),
                      
                      (T.MEASURE_MET_CAL, [T.TST_MET_CAL_CAM_CONNECTION, T.TASK_REFERENCE]),
                      
                      (T.MEASURE_MET_HEIGHT, [T.TST_MET_HEIGHT_CAM_CONNECTION, T.TASK_REFERENCE]),
                      
                      (T.MEASURE_PUPIL_ALGN, [T.TST_PUPIL_ALGN_CAM_CONNECTION, T.TASK_REFERENCE]),
                      
                      (T.MEASURE_ALL, [ T.TST_GATEWAY_CONNECTION       , 
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
                      
                      (TASK_EVAL_ALL, [T.EVAL_DATUM_REP               , 
                                       T.EVAL_MET_CAL                 , 
                                       T.EVAL_POS_REP                 , 
                                       T.EVAL_MET_HEIGHT              , 
                                       T.EVAL_PUPIL_ALGN              ,    ]),

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


