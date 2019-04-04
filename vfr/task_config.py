from __future__ import absolute_import, division, print_function

from vfr.db.colldect_limits import get_colldect_passed_p
from vfr.db.datum import get_datum_passed_p
from vfr.db.datum_repeatability import get_datum_repeatability_passed_p
from vfr.db.positional_repeatability import get_positional_repeatability_passed_p
from vfr.db.pupil_alignment import get_pupil_alignment_passed_p


class T:
    # evaluation of measurements
    EVAL_DATUM_REP = "eval_datum_rep"
    EVAL_MET_CAL = "eval_met_cal"
    EVAL_MET_HEIGHT = "eval_met_height"
    EVAL_POS_REP = "eval_pos_rep"
    EVAL_POS_VER = "eval_pos_ver"
    EVAL_PUP_ALGN = "eval_pup_aln"
    # measurements
    MEASURE_DATUM_REP = "measure_datum_rep"
    MEASURE_MET_CAL = "measure_met_cal"
    MEASURE_MET_HEIGHT = "measure_met_height"
    MEASURE_POS_REP = "measure_pos_rep"
    MEASURE_POS_VER = "measure_pos_ver"
    MEASURE_PUP_ALGN = "measure_pup_aln"
    # conditional dependencies (can be skipped if done once)
    REQ_DATUM_PASSED = "req_datum_passed"
    REQ_COLLDECT_PASSED = "req_colldect_passed"
    REQ_DATUM_REP_PASSED = "req_datum_repeatability_passed"
    REQ_FUNCTIONAL_PASSED = "req_functional_test_passed"
    REQ_POS_REP_PASSED = "req_positional_repeatability_passed"
    REQ_PUP_ALGN_PASSED = "req_pupil_alnment_passed"
    # tasks which pack measurements and evaluation in pairs
    TASK_MEASURE_NONFIBRE = "measure_nonfibre"
    TASK_MEASURE_ALL = "measure_all"
    TASK_EVAL_ALL = "eval_all"
    TASK_EVAL_NONFIBRE = "eval_nonfibre"
    TASK_INIT_GD = "initialize_grid_driver"
    TASK_INIT_RD = "initialize_unprotected_fpu_driver"
    TASK_REFERENCE = "reference"
    TASK_SELFTEST = "selftest"
    TASK_SELFTEST_NONFIBRE = "selftest_nonfibre"
    TASK_SELFTEST_FIBRE = "selftest_fibre"
    TASK_REPORT = "report"
    TASK_DUMP = "dump"
    TASK_PARK_FPUS = "park_fpus"
    TASK_REWIND_FPUS = "rewind_fpus"
    # elementary tests
    TST_ALPHA_MAX = "search_alpha_max"
    TST_ALPHA_MIN = "search_alpha_min"
    TST_BETA_MAX = "search_beta_max"
    TST_BETA_MIN = "search_beta_min"
    TST_CAN_CONNECTION = "test_can_connection"
    TST_COLLDETECT = "test_collision_detection"
    TST_DATUM = "test_datum"
    TST_DATUM_ALPHA = "test_datum_alpha"
    TST_DATUM_BETA = "test_datum_beta"
    TST_DATUM_BOTH = "test_datum_both"
    TST_DATUM_REP = "test_datum_rep"
    TST_FLASH = "flash"
    TST_FUNCTIONAL = "test_functional"
    TST_GATEWAY_CONNECTION = "test_gateway_conn"
    TST_INIT = "initiate"
    TST_INITPOS = "setpos"
    TST_LIMITS = "test_limits"
    TST_MET_CAL = "test_met_cal"
    TST_MET_CAL_CAM_CONNECTION = "test_met_cam_conn"
    TST_MET_HEIGHT = "test_met_height"
    TST_MET_HEIGHT_CAM_CONNECTION = "test_met_hght_cam_conn"
    TST_POS_REP = "test_pos_rep"
    TST_POS_REP_CAM_CONNECTION = "test_pos_rep_cam_conn"
    TST_POS_VER = "test_pos_ver"
    TST_PUP_ALGN = "test_pup_aln"
    TST_PUP_ALGN_CAM_CONNECTION = "test_pup_algn_cam_conn"


usertasks = set(
    [
        T.EVAL_DATUM_REP,
        T.EVAL_MET_CAL,
        T.EVAL_MET_HEIGHT,
        T.EVAL_POS_REP,
        T.EVAL_POS_VER,
        T.EVAL_PUP_ALGN,
        T.TASK_EVAL_ALL,
        T.TASK_EVAL_NONFIBRE,
        T.TASK_MEASURE_ALL,
        T.MEASURE_DATUM_REP,
        T.MEASURE_MET_CAL,
        T.MEASURE_MET_HEIGHT,
        T.MEASURE_POS_REP,
        T.MEASURE_POS_VER,
        T.MEASURE_PUP_ALGN,
        T.TST_FLASH,
        T.TASK_DUMP,
        T.TASK_MEASURE_NONFIBRE,
        T.TASK_REFERENCE,
        T.TASK_REPORT,
        T.TASK_SELFTEST,
        T.TASK_SELFTEST_NONFIBRE,
        T.TASK_SELFTEST_FIBRE,
        T.TASK_PARK_FPUS,
        T.TASK_REWIND_FPUS,
        T.TST_ALPHA_MAX,
        T.TST_ALPHA_MIN,
        T.TST_BETA_MAX,
        T.TST_BETA_MIN,
        T.TST_CAN_CONNECTION,
        T.TST_COLLDETECT,
        T.TST_DATUM,
        T.TST_DATUM_ALPHA,
        T.TST_DATUM_BETA,
        T.TST_DATUM_BOTH,
        T.TST_DATUM_REP,
        T.TST_FLASH,
        T.TST_FUNCTIONAL,
        T.TST_GATEWAY_CONNECTION,
        T.TST_INIT,
        T.TST_INITPOS,
        T.TST_LIMITS,
        T.TST_MET_CAL,
        T.TST_MET_CAL_CAM_CONNECTION,
        T.TST_MET_HEIGHT_CAM_CONNECTION,
        T.TST_MET_HEIGHT,
        T.TST_POS_REP,
        T.TST_POS_REP_CAM_CONNECTION,
        T.TST_POS_VER,
        T.TST_PUP_ALGN,
        T.TST_PUP_ALGN_CAM_CONNECTION,
        T.TASK_EVAL_ALL,
    ]
)


# task dependencies (where doing one task requires doing another task before)
task_dependencies = [
    (T.TST_CAN_CONNECTION, [T.TST_GATEWAY_CONNECTION, T.TASK_INIT_RD]),
    (T.TST_FLASH, [T.TASK_INIT_RD, T.TST_CAN_CONNECTION]),
    (T.TST_INITPOS, []),
    (T.TASK_SELFTEST, [T.TASK_SELFTEST_NONFIBRE, T.TASK_SELFTEST_FIBRE]),
    (
        T.TASK_SELFTEST_NONFIBRE,
        [
            T.TASK_INIT_GD,
            T.TST_MET_CAL_CAM_CONNECTION,
            T.TST_GATEWAY_CONNECTION,
            T.TST_POS_REP_CAM_CONNECTION,
            T.REQ_DATUM_PASSED,
        ],
    ),
    (
        T.TASK_SELFTEST_FIBRE,
        [
            T.TASK_INIT_GD,
            T.TST_PUP_ALGN_CAM_CONNECTION,
            T.TST_MET_CAL_CAM_CONNECTION,
            T.TST_GATEWAY_CONNECTION,
            T.REQ_DATUM_PASSED,
        ],
    ),
    (T.TASK_INIT_GD, [T.TASK_PARK_FPUS]),
    (T.TST_DATUM_ALPHA, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.TASK_REWIND_FPUS]),
    (T.TST_DATUM_BETA, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.TASK_REWIND_FPUS]),
    (T.TST_DATUM_BOTH, [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.TASK_REWIND_FPUS]),
    (
        T.TST_ALPHA_MAX,
        [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.REQ_DATUM_PASSED, T.TASK_REFERENCE],
    ),
    (
        T.TST_ALPHA_MIN,
        [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.REQ_DATUM_PASSED, T.TASK_REFERENCE],
    ),
    (
        T.TST_BETA_MAX,
        [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.REQ_DATUM_PASSED, T.TASK_REFERENCE],
    ),
    (
        T.TST_BETA_MIN,
        [T.TASK_INIT_GD, T.TST_CAN_CONNECTION, T.REQ_DATUM_PASSED, T.TASK_REFERENCE],
    ),
    (T.TASK_REFERENCE, [T.REQ_DATUM_PASSED]),
    (T.TST_COLLDETECT, [T.REQ_DATUM_PASSED, T.TASK_REFERENCE]),
    (
        T.MEASURE_DATUM_REP,
        [
            T.TASK_SELFTEST_NONFIBRE,
            T.TST_POS_REP_CAM_CONNECTION,
            T.REQ_DATUM_PASSED,
            T.REQ_COLLDECT_PASSED,
            T.TASK_REFERENCE,
        ],
    ),
    (
        T.MEASURE_POS_REP,
        [
            T.TASK_SELFTEST_NONFIBRE,
            T.TST_POS_REP_CAM_CONNECTION,
            T.TASK_REFERENCE,
            T.REQ_DATUM_PASSED,
            T.REQ_COLLDECT_PASSED,
            # T.REQ_PUP_ALGN_PASSED,
            T.REQ_DATUM_REP_PASSED,
        ],
    ),
    (
        T.MEASURE_POS_VER,
        [
            T.TASK_SELFTEST_NONFIBRE,
            T.TST_POS_REP_CAM_CONNECTION,
            T.REQ_DATUM_PASSED,
            T.REQ_COLLDECT_PASSED,
            # T.REQ_PUP_ALGN_PASSED,
            T.REQ_DATUM_REP_PASSED,
            T.REQ_POS_REP_PASSED,
            T.TASK_REFERENCE,
        ],
    ),
    (T.MEASURE_MET_CAL, [T.TASK_SELFTEST_FIBRE, T.TST_MET_CAL_CAM_CONNECTION]),
    (T.MEASURE_MET_HEIGHT, [T.TASK_SELFTEST_NONFIBRE, T.TST_MET_HEIGHT_CAM_CONNECTION]),
    (
        T.MEASURE_PUP_ALGN,
        [
            T.TASK_SELFTEST_FIBRE,
            T.TST_PUP_ALGN_CAM_CONNECTION,
            T.REQ_DATUM_PASSED,
            T.REQ_COLLDECT_PASSED,
            T.TASK_REFERENCE,
        ],
    ),
    (
        T.TASK_MEASURE_ALL,
        [
            T.TASK_SELFTEST,
            T.TST_GATEWAY_CONNECTION,
            T.TST_CAN_CONNECTION,
            T.TST_POS_REP_CAM_CONNECTION,
            T.TST_MET_CAL_CAM_CONNECTION,
            T.TST_MET_HEIGHT_CAM_CONNECTION,
            T.TST_PUP_ALGN_CAM_CONNECTION,
            T.TST_DATUM,
            T.TST_LIMITS,
            T.MEASURE_DATUM_REP,
            T.TST_MET_CAL,
            T.MEASURE_MET_CAL,
            T.TST_POS_REP,
            T.MEASURE_POS_REP,
            T.TST_POS_VER,
            T.MEASURE_MET_HEIGHT,
            T.TST_PUP_ALGN,
            T.MEASURE_PUP_ALGN,
        ],
    ),
    (
        T.TASK_MEASURE_NONFIBRE,
        [
            T.TASK_SELFTEST,
            T.TST_GATEWAY_CONNECTION,
            T.TST_CAN_CONNECTION,
            T.TST_POS_REP_CAM_CONNECTION,
            T.TST_MET_CAL_CAM_CONNECTION,
            T.TST_MET_HEIGHT_CAM_CONNECTION,
            T.TST_PUP_ALGN_CAM_CONNECTION,
            T.TST_DATUM,
            T.TST_LIMITS,
            T.MEASURE_DATUM_REP,
            T.TST_POS_REP,
            T.MEASURE_POS_REP,
            T.TST_POS_VER,
            T.MEASURE_MET_HEIGHT,
        ],
    ),
    (
        T.TASK_EVAL_ALL,
        [
            T.EVAL_DATUM_REP,
            T.EVAL_MET_CAL,
            T.EVAL_POS_REP,
            T.EVAL_POS_VER,
            T.EVAL_MET_HEIGHT,
            T.EVAL_PUP_ALGN,
        ],
    ),
    (
        T.TASK_EVAL_NONFIBRE,
        [T.EVAL_DATUM_REP, T.EVAL_POS_REP, T.EVAL_POS_VER, T.EVAL_MET_HEIGHT],
    ),
]

# conditional dependencies which are skipped if last test was already
# passed for all FPUs, otherwise the listed tasks are addded.
conditional_dependencies = [
    (T.REQ_DATUM_REP_PASSED, get_datum_repeatability_passed_p, [T.TST_DATUM_REP]),
    (T.REQ_DATUM_PASSED, get_datum_passed_p, [T.TST_DATUM]),
    (T.REQ_COLLDECT_PASSED, get_colldect_passed_p, [T.TST_COLLDETECT]),
    (T.REQ_PUP_ALGN_PASSED, get_pupil_alignment_passed_p, [T.TST_PUP_ALGN]),
    (T.REQ_POS_REP_PASSED, get_positional_repeatability_passed_p, [T.TST_POS_REP]),
]


# task expansions (where one user-selectable task contains several sub-tasks)
task_expansions = [
    (T.TST_INIT, [T.TST_FLASH, T.TST_INITPOS]),
    (T.TST_DATUM, [T.TST_DATUM_ALPHA, T.TST_DATUM_BETA, T.TST_DATUM_BOTH]),
    (
        T.TST_LIMITS,
        [
            T.TST_COLLDETECT,
            T.TST_ALPHA_MAX,
            T.TST_ALPHA_MIN,
            T.TST_BETA_MAX,
            T.TST_BETA_MIN,
        ],
    ),
    (
        T.TST_FUNCTIONAL,
        [T.TST_GATEWAY_CONNECTION, T.TST_CAN_CONNECTION, T.TST_DATUM, T.TST_LIMITS],
    ),
    (T.TST_DATUM_REP, [T.MEASURE_DATUM_REP, T.EVAL_DATUM_REP]),
    (T.TST_MET_CAL, [T.MEASURE_MET_CAL, T.EVAL_MET_CAL]),
    (T.TST_MET_HEIGHT, [T.MEASURE_MET_HEIGHT, T.EVAL_MET_HEIGHT]),
    (T.TST_POS_REP, [T.MEASURE_POS_REP, T.EVAL_POS_REP]),
    (T.TST_POS_VER, [T.MEASURE_POS_VER, T.EVAL_POS_VER]),
    (T.TST_PUP_ALGN, [T.MEASURE_PUP_ALGN, T.EVAL_PUP_ALGN]),
]
