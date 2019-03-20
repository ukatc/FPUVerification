# -*- coding: utf-8-unix -*-

from __future__ import print_function, division
from os import environ
from argparse import Namespace
from math import ceil
from numpy import NaN, Inf

DEFAULT_TASKS = ["selftest", "measure_all", "evaluate_all", "report"]


INSTRUMENT_FOCAL_LENGTH = 4101.4  # millimeter (does not change)

ALPHA_DATUM_OFFSET = -180

PROTECTION_TOLERANCE = 0.15 # degrees of protection between measured
                            # limit and soft protection range

DB_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.~%Z" # "~" means number of milliseconds

LAMP_WARMING_TIME_MILLISECONDS = 1000.0

NR360_SERIALNUMBER = 40873952

MTS50_SERIALNUMBER = 83822910

IMAGE_ROOT_FOLDER = environ.get("IMAGE_ROOT_FOLDER", "/moonsdata/verification/images")

POS_REP_CAMERA_IP_ADDRESS = "169.254.187.121"

MET_CAL_CAMERA_IP_ADDRESS = "169.254.189.121"

MET_HEIGHT_CAMERA_IP_ADDRESS = "169.254.190.121"

PUP_ALGN_CAMERA_IP_ADDRESS = "169.254.108.113"


METROLOGY_CAL_POSITIONS = [268, 328, 28, 88, 148, 208]

COLLDECT_MEASUREMENT_PARS = Namespace(
    COLDECT_ALPHA=-180,
    COLDECT_BETA=70,
    COLDECT_POSITIONS=[NaN, NaN, NaN, NaN, NaN, NaN],
    LIMIT_ALPHA_NEG_EXPECT=-182.0,
    LIMIT_ALPHA_POS_EXPECT=+175.0,
    LIMIT_BETA_NEG_EXPECT=-185.0,
    LIMIT_BETA_POS_EXPECT=+155.0,
)

DATUM_REP_MEASUREMENT_PARS = Namespace(
    DATUM_REP_ITERATIONS=10,  # the
    # number of datum operations made for
    # each test
    DATUM_REP_PASS=20.0,  # the maximum single
    # deviation in microns from the
    # baseline position which represents an
    # acceptable FPU
    DATUM_REP_EXPOSURE_MS=500,  # the exposure
    # time in milliseconds for a correctly
    # exposed image
    DATUM_REP_POSITIONS=METROLOGY_CAL_POSITIONS,
)


MET_CAL_MEASUREMENT_PARS = Namespace(
    METROLOGY_CAL_POSITIONS=METROLOGY_CAL_POSITIONS,
    # rotary stage angle, in degrees, required to place each FPU under
    # the metrology calibration camera
    METROLOGY_CAL_TARGET_EXPOSURE_MS=500.0,  # he exposure time in
    # milliseconds for a
    # correctly exposed
    # image of the
    # illuminated targets
    METROLOGY_CAL_FIBRE_EXPOSURE_MS=0.1,  # he exposure time in
    # milliseconds for a
    # correctly exposed image
    # of the illuminated
    # targets
    METROLOGY_CAL_BACKLIGHT_VOLTAGE=0.1,  # voltage of backlight
    # for fibre measurements
)

POS_REP_PLATESCALE = 0.02361  # millimeter per pixel

POS_REP_CALIBRATION_PARS = {
    "algorithm": "scale",
    "scale_factor": POS_REP_PLATESCALE,
    # values below are placeholders
    "coeffs": [[NaN, NaN, NaN], [NaN, NaN, NaN], [NaN, NaN, NaN]],
}


POS_REP_ANALYSIS_PARS = Namespace(
    POS_REP_PLATESCALE=POS_REP_PLATESCALE,
    POS_REP_SMALL_DIAMETER=1.5,  # millimeter
    POS_REP_LARGE_DIAMETER=2.5,  # millimeter
    POS_REP_DIAMETER_TOLERANCE=0.1,  # millimeter
    POS_REP_THRESHOLD=40,  # 0-255
    POS_REP_QUALITY_METRIC=0.8,  # dimensionless
    POS_REP_CALIBRATION_PARS=POS_REP_CALIBRATION_PARS,
    display=False,
    verbosity=0,
)

MET_CAL_TARGET_ANALYSIS_PARS = Namespace(
    MET_CAL_PLATESCALE=0.00668,  # millimeter per pixel
    MET_CAL_SMALL_DIAMETER=1.5,  # millimeter
    MET_CAL_LARGE_DIAMETER=2.5,  # millimeter
    MET_CAL_DIAMETER_TOLERANCE=0.1,  # millimeter
    MET_CAL_GAUSS_BLUR=3,  # pixels - MUST BE AN ODD NUMBER
    MET_CAL_THRESHOLD=40,  # 0-255
    MET_CAL_QUALITY_METRIC=0.8,  # dimensionless
    display=False,  # will display image with contours annotated
    verbosity=0,
)

MET_CAL_FIBRE_ANALYSIS_PARS = Namespace(
    MET_CAL_PLATESCALE=0.00668,  # millimeter per pixel
    MET_CAL_QUALITY_METRIC=0.8,  # dimensionless
    display=False,  # will display image with contours annotated
    verbosity=0,
)


POS_REP_POSITIONS = [132, 192, 252, 312, 12, 72]

# these values are for CAN protocol version 1 firmware
MOTOR_MIN_STEP_FREQUENCY = 500
MOTOR_MAX_STEP_FREQUENCY = 2000
MOTOR_MAX_START_FREQUENCY = 550
WAVEFORM_SEGMENT_LENGTH_MS = 250
STEPS_LOWER_LIMIT = int(MOTOR_MIN_STEP_FREQUENCY * WAVEFORM_SEGMENT_LENGTH_MS / 1000)
STEPS_UPPER_LIMIT = int(
    ceil(MOTOR_MAX_STEP_FREQUENCY * WAVEFORM_SEGMENT_LENGTH_MS / 1000)
)


POS_REP_MEASUREMENT_PARS = Namespace(
    POS_REP_POSITIONS=POS_REP_POSITIONS,  # the rotary stage angle required to
    # place each FPU under the positional
    # repeatability camera
    POS_REP_EXPOSURE_MS=NaN,  # the exposure time in
    # milliseconds for a correctly
    # exposed image
    POS_REP_NUM_INCREMENTS=NaN,  # the number of movements made
    # within each positive sweep from
    # the starting position
    POS_REP_ITERATIONS=NaN,  # the number of times each FPU
    # sweeps back and forth
    POS_REP_SAFETY_MARGIN=5.0,  # safety margin, in degree, for
    # distance to range limits when testing
    POS_REP_WAVEFORM_PARS={
        "mode": "fast",
        "max_change": 1.2,
        "min_steps": STEPS_LOWER_LIMIT,
        "max_steps": STEPS_UPPER_LIMIT,
        "max_change_alpha": None,
        "max_acceleration_alpha": None,
        "max_deceleration_alpha": None,
        "min_steps_alpha": None,
        "min_stop_steps_alpha": None,
        "max_steps_alpha": None,
        "max_change_beta": None,
        "max_acceleration_beta": None,
        "max_deceleration_beta": None,
        "min_steps_beta": None,
        "min_stop_steps_beta": None,
        "max_steps_beta": None,
        "max_change": 1.2,
        "max_acceleration": 35,
        "max_deceleration": 35,
        "min_steps": STEPS_LOWER_LIMIT,
        "min_stop_steps": None,
        "max_steps": STEPS_UPPER_LIMIT,
    },
)


POS_REP_EVALUATION_PARS = Namespace(
    POS_REP_PASS=NaN,  # the maximum angular deviation, in
    # degrees, from an average position of
    # a grouping of measured points at a
    # given nominal position which
    # represents an acceptable FPU
)


POS_VER_MEASUREMENT_PARS = Namespace(
    POS_REP_POSITIONS=POS_REP_POSITIONS,  # the rotary stage angle required to
    # place each FPU under the positional
    # repeatability camera
    POSITION_VER_EXPOSURE_MS=NaN,  # the exposure time in
    # milliseconds for a correctly
    # exposed image
    POSITION_VER_ITERATIONS=NaN,  # the number of times each FPU
    # sweeps back and forth
)


POS_VER_EVALUATION_PARS = Namespace(
    POSITION_VER_PASS=NaN,  # the maximum angular deviation, in
    # degrees, from an average position of
    # a grouping of measured points at a
    # given nominal position which
    # represents an acceptable FPU
)


PUP_ALGN_MEASUREMENT_PARS = Namespace(
    PUP_ALGN_POSITIONS=[
        0.0,
        NaN,
        NaN,
        NaN,
        NaN,
        NaN,
    ],  # the rotary stage angle required to
    # place each FPU under the first pupil
    # alignment fold mirror
    PUP_ALGN_LINPOSITIONS=[  # the linear stage positions
        0.0,  # note= bogus values - spec missing FIXME
        5.0,
        10.0,
        15.0,
        20.0,
        25.0,
    ],
    # required to illuminate each FPU
    # fibre
    PUP_ALGN_EXPOSURE_MS=NaN,  # the exposure time in milliseconds
    # for a correctly exposed image
)

PUP_ALGN_PLATESCALE = 0.00668

PUP_ALGN_CALIBRATION_PARS = {
    "algorithm": "scale",
    "scale_factor": PUP_ALGN_PLATESCALE,
    # values below are placeholders
    "coeffs": [[NaN, NaN, NaN], [NaN, NaN, NaN], [NaN, NaN, NaN]],
}


PUP_ALGN_ANALYSIS_PARS = Namespace(
    PUP_ALGN_PLATESCALE=PUP_ALGN_PLATESCALE,  # millimeter per pixel
    PUP_ALGN_CIRCULARITY_THRESH=0.8,  # dimensionless
    PUP_ALGN_NOISE_METRIC=0,
    PUP_ALGN_CALIBRATION_PARS=PUP_ALGN_CALIBRATION_PARS,
    display=False,
    verbosity=0,
)


PUP_ALGN_EVALUATION_PARS = Namespace(
    PUP_ALGN_CALIBRATED_CENTRE_X=0.0,
    PUP_ALGN_CALIBRATED_CENTRE_Y=-0.0,
    PUPIL_ALN_PASS=Inf,  # the maximum total deviation in arcmin
    # from the calibrated centre point which
    # represents an acceptable FPU
)


MET_HEIGHT_MEASUREMENT_PARS = Namespace(
    MET_HEIGHT_POSITIONS=[
        268,
        328,
        28,
        88,
        148,
        208,
    ],  # the rotary stage angle required to place each FPU
    #                                                        in front of the metrology height camera
    MET_HEIGHT_TARGET_EXPOSURE_MS=NaN,  # the exposure time in
    # milliseconds for a
    # correctly exposed image
    # of the illuminated
    # targets
)


MET_HEIGHT_ANALYSIS_PARS = Namespace(
    METHT_PLATESCALE=0.00668,  # millimeter per pixel
    METHT_THRESHOLD=150,  # 0-255
    METHT_SCAN_HEIGHT=2000,  # pixels
    METHT_GAUSS_BLUR=1,  # pixels - MUST BE AN ODD NUMBER
    METHT_STANDARD_DEV=0.04,  # millimeter
    METHT_NOISE_METRIC=0.25,  # dimensionless
    display=False,
    verbosity=0,
)

MET_HEIGHT_EVALUATION_PARS = Namespace(
    METHT_HEIGHT_TOLERANCE=NaN  # maximum allowable height of both targets, in millimeter
)
