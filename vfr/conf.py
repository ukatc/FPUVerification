from __future__ import print_function, division

TST_GATEWAY_CONNECTION = "test_gateway_connection"
TST_CAN_CONNECTION     = "test_can_connection"
TST_DATUM              = "test_datum"
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
                 TST_ALPHA_MAX,
                 TST_BETA_MAX,
                 TST_BETA_MIN]

ALPHA_DATUM_OFFSET = -180
 
DB_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%Z'
