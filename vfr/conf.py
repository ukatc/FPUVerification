from __future__ import print_function, division


ALPHA_DATUM_OFFSET = -180
 
DB_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%Z'

NR360_SERIALNUMBER = 40873952

IMAGE_ROOT_FOLDER = '/moonsdata/verification/images'

POS_REP_CAMERA_IP_ADDRESS = "169.254.187.121"

MET_CAL_CAMERA_IP_ADDRESS = "8.8.8.8"

MET_HEIGHT_CAMERA_IP_ADDRESS = "8.8.8.8"

PUPIL_ALGN_CAMERA_IP_ADDRESS = "8.8.8.8"

DATUM_REP_MEASUREMENT_PARS = { 'DATUM_REP_ITERATIONS' : 10, #  – the number of datum operations made for each test
                   'DATUM_REP_PASS' : 20.0 ,  # – the maximum single deviation in microns from the baseline position which represents an acceptable FPU
                   'DATUM_REP_EXPOSURE_MS' : 500, # – the exposure time in milliseconds for a correctly exposed image
                   'POS_REP_POSITIONS' : [14 + k * 30 for  k in range(6)],
}


MET_CAL_MEASUREMENT_PARS = {
    'METROLOGY_CAL_POSITIONS' = [14 + k * 30 for  k in range(6)], # the rotary stage angle, in degrees, required to place
    #                                                             each FPU under the metrology calibration camera
    'METROLOGY_CAL_TARGET_EXPOSURE_MS' = 500.0, # he exposure time in milliseconds for a correctly
    #                                        exposed image of the illuminated targets
    'METROLOGY_CAL_FIBRE_EXPOSURE_MS' = 0.1, # he exposure time in milliseconds for a correctly
    #                                        exposed image of the illuminated targets
    'METROLOGY_CAL_BACKLIGHT_VOLTAGE' = 0.1, # voltage of backlight for fibre measurements
}


POSREP_ANALYSIS_PARS = {
    'POSREP_SMALL_TARGET_DIA_LOWER_THRESH' : NaN,
    'POSREP_SMALL_TARGET_DIA_UPPER_THRESH' : NaN,
    'POSREP_LARGE_TARGET_DIA_LOWER_THRESH' : NaN,
    'POSREP_LARGE_TARGET_DIA_UPPER_THRESH' : NaN,
    'POSREP_TARGET_CIRCULARITY_THRESH' : NaN,
    'POSREP_THRESHOLD_VAL' : NaN,
    'POSREP_PLATESCALE' : NaN,
    'POSREP_DISTORTION_MATRIX' : NaN,
}

METCAL_ANALYSIS_PARS = {
    'METCAL_SMALL_TARGET_DIA_LOWER_THRESH' : NaN,
    'METCAL_SMALL_TARGET_DIA_UPPER_THRESH' : NaN,
    'METCAL_LARGE_TARGET_DIA_LOWER_THRESH' : NaN,
    'METCAL_LARGE_TARGET_DIA_UPPER_THRESH' : NaN,
    'METCAL_TARGET_CIRCULARITY_THRESH' : NaN,
    'METCAL_THRESHOLD_VAL' : NaN,
    'METCAL_PLATESCALE' : NaN,
}

METCAL_FIBRE_ANALYSIS_PARS = {'METCAL_FIND_GAUSSIAN_BOX_SIZE' : nan,
                              'METCAL_PLATESCALE' : nan}
