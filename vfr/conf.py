from __future__ import print_function, division

TST_GATEWAY_CONNECTION = "test_gateway_connection"
TST_CAN_CONNECTION     = "test_can_connection"
TST_DATUM              = "test_datum"
TST_CDECT              = "test_collision_detection"
TST_ALPHA_MIN          = "test_alpha_min"
TST_ALPHA_MAX          = "test_alpha_max"
TST_BETA_MAX           = "test_beta_max"
TST_BETA_MIN           = "test_beta_min"
TST_FUNCTIONAL         = "test_functional"
TST_INIT               = "init"
TST_FLASH              = "flash_snum"
TST_INITPOS            = "init_positions"
TST_LIMITS             = "test_limits"

DEFAULT_TASKS = [TST_GATEWAY_CONNECTION,
                 TST_CAN_CONNECTION,
                 TST_FLASH,
                 TST_INITPOS,
                 TST_DATUM,
                 TST_CDECT,
                 TST_ALPHA_MAX,
                 TST_BETA_MAX,
                 TST_BETA_MIN]

ALPHA_DATUM_OFFSET = -180
 
DB_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%Z'

NR360_SERIALNUMBER = 40873952

IMAGE_FOLDER = '/moonsdata/verification/images'

POS_REP_CAMERA_IP_ADDRESS = "169.254.187.121"

DATUM_REP_PARS = { 'DATUM_REP_ITERATIONS' : 10, #  – the number of datum operations made for each test
                   'DATUM_REP_PASS' : 20.0 ,  # – the maximum single deviation in microns from the baseline position which represents an acceptable FPU
                   'DATUM_REP_EXPOSURE_MS' : 500, # – the exposure time in milliseconds for a correctly exposed image
                   'POS_REP_POSITIONS' : [14 + k * 30 for  k in range(6)],
}
