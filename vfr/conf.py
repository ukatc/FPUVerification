# -*- coding: utf-8 -*
#
# MOONS Verification Rig Configuration Parameters.
#
# This file can be used to define global parameters or control the
# default behaviour of the verification rig software.
#
from __future__ import absolute_import, division, print_function

from argparse import Namespace
from math import ceil
import os

from numpy import Inf

# Define the default tasks to be executed (if no tasks are specified explicitly).
# Used by vfr/options.py
DEFAULT_TASKS = ["selftest", "test_functional", "measure_all", "eval_all", "report"]
DEFAULT_TASKS_NONFIBRE = [
    "selftest_nonfibre",
    "test_functional",
    "measure_nonfibre",
    "eval_nonfibre",
    "report",
]

# A few parameters are defined globally because they are used in many
# different places

# Turn on graphical diagnostics. Set to True only if you are running the
# software interactively and would like to see diagnostic graphics. Set
# to False if the software is to be run unattended.
GRAPHICAL_DIAGNOSTICS = False

# The minimum number of points for a good circle fit
MIN_POINTS_FOR_CIRCLE_FIT = 6

# NOTE: ALPHA_DATUM_OFFSET is also defined in fpu_commands.py.
#       Why is it repeated here? Be aware of the two values getting out of step.
#       This version is not used by the gearbox calibration.
ALPHA_DATUM_OFFSET = -180
ALPHA_RANGE_MAX = 155.0  # Maximum range of alpha arm (deg)

# Angle of protection (deg) between measured limit and soft protection range.
PROTECTION_TOLERANCE = 0.15  

DB_TIME_FORMAT = "%Y-%m-%dT%H.%M.%S.~%Z"  # "~" means number of milliseconds

LAMP_WARMING_TIME_MILLISECONDS = 1000.0

NR360_SERIALNUMBER = 40873952

MTS50_SERIALNUMBER = 83822910

# If you work on another machine (for example testing image analysis
# scripts), you should set the environment variable
# VERIFICATION_ROOT_FOLDER to the path which contains the images and
# calibration data. Shorthands like ~/, ~user, or ${HOME} are expanded
# before use.
VERIFICATION_ROOT_FOLDER = os.environ.get(
    "VERIFICATION_ROOT_FOLDER", "/moonsdata/verification/"
)

# IP addresses of the verification rig devices.
POS_REP_CAMERA_IP_ADDRESS    = "169.254.187.121"
MET_CAL_CAMERA_IP_ADDRESS    = "169.254.189.121"
MET_HEIGHT_CAMERA_IP_ADDRESS = "169.254.190.121"
PUP_ALGN_CAMERA_IP_ADDRESS   = "169.254.108.113"

# The relative weight of large vs small metrology target position.
# Weighting greater than 0.5 favours the larger blob.
# Used in Gearbox/gear_correction.py.
BLOB_WEIGHT_FACTOR = 0.75

# The list of percentiles to be included in the statistics reported by the
# positional repeatability and positional verification evaluation tasks.
PERCENTILE_ARGS = [50, 90, 95, 97.5]

# Go to these angles before beginning a datum search.
REWIND_POS_ALPHA = -175.0  # Alpha start position before initial datum search
REWIND_POS_BETA = 1.0      # Beta start position before initial datum search

# Stage positions used to capture metrology calibration information.
# Used in ./vfr/verification_tasks/metrology_calibration.py
METROLOGY_CAL_POSITIONS = [254.0, 314.5, 13.0, 73.0, 133.5]

# The expected size and separation of the metrology targets and the thresholds
# used by the image analysis software (ImageAnalysisFuncs/target_detection_otsu.py).
LARGE_TARGET_RADIUS = 1.25 # mm
SMALL_TARGET_RADIUS = 0.75 # mm
TARGET_SEPERATION = 2.37 # mm - The distance between the centers
THRESHOLD_LIMIT = 60 # pixel values for Pos_rep camera
DAT_REP_THRESHOLD_LIMIT = 100 # pixel threshold values for dat rep camera

#
# Related sets of configuration parameters are grouped into namespaces.
#

#
# Collision detection parameter set.
# ----------------------------------
COLLDECT_MEASUREMENT_PARS = Namespace(
    COLDECT_ALPHA=-180,
    COLDECT_BETA=130,
    COLDECT_BETA_SPAN=25.0,
    COLDECT_POSITIONS=[198, 258, 318.5, 17, 77],
    LIMIT_ALPHA_NEG_EXPECT=-182.0,
    LIMIT_ALPHA_POS_EXPECT=+175.0,
    LIMIT_BETA_NEG_EXPECT=-190.0,
    LIMIT_BETA_POS_EXPECT=+165.0,
    RECOVERY_ANGLE_DEG=3.0,  # angle (in degrees) of back movement to recover
)

#
# Datum repeatability data collection parameter sets.
# ---------------------------------------------------
DATUM_REP_MEASUREMENT_PARS = Namespace(
    EXERCISE_FPU=True,  # Start by moving FPU to reduce stiction
    DATUM_TWICE=True,   # Find datum twice to improve accuracy?
    # The number of datum operations made for each test
    DATUM_REP_ITERATIONS=10,
    # The exposure time in milliseconds for a correctly exposed image
    DATUM_REP_EXPOSURE_MS=1300,  
    DATUM_REP_POSITIONS=METROLOGY_CAL_POSITIONS,
)

#
# NOTE: The following parameters define a default plate scale which
# is only used if a camera calibration file is not found.
#
DAT_REP_PLATESCALE = (
    0.00693
)  # millimeter per pixel, for the metrology calibration camera

DAT_REP_CALIBRATION_PARS = {"algorithm": "scale", "scale_factor": DAT_REP_PLATESCALE}

DAT_REP_TARGET_DETECTION_OTSU_PARS = Namespace(
    CALIBRATION_PARS=DAT_REP_CALIBRATION_PARS,
    SMALL_RADIUS=SMALL_TARGET_RADIUS,  # in mm
    LARGE_RADIUS=LARGE_TARGET_RADIUS,  # in mm
    GROUP_RANGE=TARGET_SEPERATION,  # in mm
    THRESHOLD_LIMIT=DAT_REP_THRESHOLD_LIMIT,
    QUALITY_METRIC=0.4,  # dimensionless
    BLOB_SIZE_TOLERANCE=0.2, # dimensionless
    GROUP_RANGE_TOLERANCE=0.2 # dimensionless
)
DAT_REP_TARGET_DETECTION_CONTOUR_PARS = Namespace(
    CALIBRATION_PARS=DAT_REP_CALIBRATION_PARS,
    SMALL_DIAMETER=1.45,  # millimeter
    LARGE_DIAMETER=2.45,  # millimeter
    DIAMETER_TOLERANCE=0.15,  # millimeter
    # THRESHOLD=60,  # 0-255
    THRESHOLD=70,  # 0-255
    QUALITY_METRIC=0.8,  # dimensionless
)

#
# Datum repeatability data analysis parameter set.
# ------------------------------------------------
# FIXME: this needs later adjustment (does not work currently). Still true??
DATUM_REP_ANALYSIS_PARS = Namespace(
    QUALITY_METRIC=0.8,  # dimensionless
    TARGET_DETECTION_ALGORITHM="otsu",  # "otsu" or "contours"
    TARGET_DETECTION_OTSU_PARS=DAT_REP_TARGET_DETECTION_OTSU_PARS,
    TARGET_DETECTION_CONTOURS_PARS=DAT_REP_TARGET_DETECTION_CONTOUR_PARS,
    PLATESCALE=DAT_REP_PLATESCALE,  # millimeter per pixel
    MAX_FAILURE_QUOTIENT=0.2,
    # The maximum single deviation in microns from the baseline position
    # which represents an acceptable FPU
    DATUM_REP_PASS=30.0,  
    DATUM_REP_TESTED_PERCENTILE=95,  # The tested percentile
    display=False,
    verbosity=0,
    loglevel=0,)

LINPOSITIONS = [  # the linear stage positions
    10.5,  # FIXME: bogus values - spec missing ??
    19.0,
    27.5,
    35.0,
    43.5,
]

#
# Metrology calbration data collection parameter sets.
# ---------------------------------------------------
MET_CAL_MEASUREMENT_PARS = Namespace(
    METROLOGY_CAL_POSITIONS=METROLOGY_CAL_POSITIONS,
    # rotary stage angle, in degrees, required to place each FPU under
    # the metrology calibration camera
    METROLOGY_CAL_TARGET_EXPOSURE_MS=1300,  # he exposure time in
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
    # Linear stage positions for fibre measurements
    METROLOGY_CAL_LINPOSITIONS=LINPOSITIONS,  # linear stage positions
)

#
# NOTE: The following parameters define a default plate scale which
# is only used if a camera calibration file is not found.
#
#MET_CAL_PLATESCALE = 0.00668  # millimeter per pixel
MET_CAL_PLATESCALE = DAT_REP_PLATESCALE  # millimeter per pixel
MET_CAL_CALIBRATION_PARS = {"algorithm": "scale", "scale_factor": MET_CAL_PLATESCALE}

MET_CAL_TARGET_DETECTION_OTSU_PARS = Namespace(
    PLATESCALE=MET_CAL_PLATESCALE,  # millimeter per pixel
    CALIBRATION_PARS=MET_CAL_CALIBRATION_PARS,
    SMALL_RADIUS=SMALL_TARGET_RADIUS,  # in mm
    LARGE_RADIUS=LARGE_TARGET_RADIUS,  # in mm
    GROUP_RANGE=TARGET_SEPERATION,  # in mm
    THRESHOLD_LIMIT=THRESHOLD_LIMIT,
    QUALITY_METRIC=0.4,  # dimensionless
    BLOB_SIZE_TOLERANCE=0.2, # dimensionless
    GROUP_RANGE_TOLERANCE=0.2 # dimensionless
)
MET_CAL_TARGET_DETECTION_CONTOUR_PARS = Namespace(
    SMALL_DIAMETER=1.42,  # millimeter
    LARGE_DIAMETER=2.42,  # millimeter
    DIAMETER_TOLERANCE=0.15,  # millimeter
    THRESHOLD=80,  # 0-255
    QUALITY_METRIC=0.8,  # dimensionless
)

#
# Metrology calbration data analysis parameter sets.
# --------------------------------------------------
MET_CAL_TARGET_ANALYSIS_PARS = Namespace(
    MET_CAL_GAUSS_BLUR=3,  # pixels - MUST BE AN ODD NUMBER
    MET_CAL_TARGET_DETECTION_ALGORITHM="otsu",  # "otsu" or "contours"
    MET_CAL_TARGET_DETECTION_OTSU_PARS=MET_CAL_TARGET_DETECTION_OTSU_PARS,
    MET_CAL_TARGET_DETECTION_CONTOUR_PARS=MET_CAL_TARGET_DETECTION_CONTOUR_PARS,
    PLATESCALE=MET_CAL_PLATESCALE,
    display=False,  # will display image with contours annotated
    verbosity=0,
    loglevel=0,
)

MET_CAL_FIBRE_ANALYSIS_PARS = Namespace(
    PLATESCALE=MET_CAL_PLATESCALE,  # millimeter per pixel
    CALIBRATION_PARS=MET_CAL_CALIBRATION_PARS,
    
    MIN_RADIUS=0.1,  # in mm
    MAX_RADIUS=1.5,  # in mm
    THRESHOLD_LIMIT=40,
    QUALITY_METRIC=0.8,  # dimensionless
    
    display=False,  # will display image with contours annotated
    verbosity=0,
    loglevel=0,
)

# The default rotary stage angles (deg) required to place each FPU under the
# positional repeatability camera.
POS_REP_POSITIONS = [135, 195, 255, 315, 15]

# These values are for CAN protocol version 1 firmware
# TODO: These parameters appear to be no longer used. Remove?
# See parameter POS_REP_WAVEFORM_PARS, below.
MOTOR_MIN_STEP_FREQUENCY = 500
MOTOR_MAX_STEP_FREQUENCY = 2000
MOTOR_MAX_START_FREQUENCY = 550
WAVEFORM_SEGMENT_LENGTH_MS = 125
STEPS_LOWER_LIMIT = int(MOTOR_MIN_STEP_FREQUENCY * WAVEFORM_SEGMENT_LENGTH_MS / 1000)
STEPS_UPPER_LIMIT = int(
    ceil(MOTOR_MAX_STEP_FREQUENCY * WAVEFORM_SEGMENT_LENGTH_MS / 1000)
)

#
# Positional repeatability data collection parameter set.
# -------------------------------------------------------
POS_REP_MEASUREMENT_PARS = Namespace(
    # The rotary stage angle (degree) required to place each FPU under the
    # positional repeatability camera.
    POS_REP_POSITIONS=POS_REP_POSITIONS,
    # The exposure time in milliseconds for a correctly exposed image.
    POS_REP_EXPOSURE_MS=200,
    # The number of low-resolution measurements made within each positive sweep
    # from the starting position.
    POS_REP_NUM_INCREMENTS=15,
    # The number of times each FPU sweeps back and forth.
    POS_REP_ITERATIONS=3,
    # The number of hi-resolution measurements made within an extra sweep from
    # the starting position.
    POS_REP_NUM_HI_RES_INCREMENTS_FACTOR=24,
    
    # The indices of the alpha and beta fixpoint positions. The fixpoint angle
    # is chosen from a fixed list of angles.
    # Should be a number between 1 and POS_REP_NUM_INCREMENTS.
    ALPHA_FIXPOINT = 10, 
    BETA_FIXPOINT = 10,
    
    # Safety margin, in degree, for distance to range limits when testing.
    POS_REP_SAFETY_MARGIN=1.0,
    # Motor waveform parameters. Now defined for CAN protocol version 2 firmware.
    POS_REP_WAVEFORM_PARS={
        "mode": "limacc",
        "max_change": 1.2,
        "min_steps": STEPS_LOWER_LIMIT,
        "max_steps": STEPS_UPPER_LIMIT,
        "min_stop_steps": None,
        "max_change_alpha": None,
        "max_acceleration_alpha": 50,
        "max_deceleration_alpha": 50,
        "min_steps_alpha": None,
        "min_stop_steps_alpha": None,
        "max_steps_alpha": None,
        "max_change_beta": None,
        "max_acceleration_beta": 50,
        "max_deceleration_beta": 50,
        "min_steps_beta": None,
        "min_stop_steps_beta": None,
        "max_steps_beta": None,
        "max_acceleration": 50,
        "max_deceleration": 50,
    },
    POS_REP_WAVEFORM_RULESET=0,  # '0' does switch off checking
    POS_REP_CALIBRATION_MAPFILE="calibration/mapping/pos-rep-2019-04-10.cfg",
    N_DATUM=3,  # Number of datumn measurements in before and after a pos_rep meaurement
    SMALL_MOVE=15,  # This distance to move between datum measurements.
)

#
# Positional repeatability data analysis parameter set.
# -----------------------------------------------------
POS_REP_EVALUATION_PARS = Namespace(
    # The maximum tolerable shift (in mm) between the centre of mass of the
    # points fitted to a circle and the fitted centre. A larger shift
    # indicates the points are too skewed to make a reliable fit.
    MAX_CENTRE_SHIFT = 2.0,

    # The maximum angle (radians) to which the camera and turntable are
    # expected to move. A camera offset fit which generates a larger
    # deviation is rejected.
    MAX_OFFSET_SHIFT_RAD = 0.15,

    # The maximum angular deviation, in degrees, from an average position of
    # a grouping of measured points at a  given nominal position which
    # represents an acceptable FPU.
    POS_REP_PASS=0.030,

    # Minimum number of samples required before a position is added to the
    # overall statistical measure. A high number restricts statistics to
    # low resolution points only. A low number includes more high resolution
    # points with fewer repeats.
    # If reduced below 5, the WEIGHTED_MEASURES flag can be set True
    # to weight the measures according to number of samples.
    # A value less than 2 is not recommended.
    MIN_NUMBER_POINTS=2,  # Was 5
    # Weight the mean and percentiles by the sample sizes.
    WEIGHTED_MEASURES=True,
    
    # Set this parameter to True to treat the alpha and beta circles as
    # ellipses (to take into account a tilt).
    APPLY_ELLIPTICAL_CORRECTION=True,
    
    # Set these parameters to True to apply the gearbox correction when
    # determining the motor angles.
    # APPLY_ELLIPTICAL_CORRECTION=False,
    APPLY_GEARBOX_CORRECTION_ALPHA=True,
    APPLY_GEARBOX_CORRECTION_BETA=True,
    # TODO: Add parameters to control whether a turntable offset is
    # applied, the order of the fit.
)

#
# Gearbox calibration data analysis parameter set.
# ------------------------------------------------
GEARBOX_CALIBRATION_PARS = Namespace(
    # The minimum number of alpha and beta points for a good gearbox calibration.
    # NOTE: The points should also evenly cover the full range of achievable angles. 
    MIN_POINTS_FOR_GEARBOX_FIT = 360,

    # Flags to modify how the gearbox calibration determines zeropoints.
    #
    # If FIX_CAMERA_OFFSET=True (recommended), the camera offset angle
    # is determined from the centres of the beta circles and then fixed.
    # If set to False, the camera offset is determined by fitting the
    # circle data.
    #
    # If FIX_BETA0=True (recommended if sufficient data measurements),
    # the beta0 offset angle is derived from datum measurements (if
    # available). If set to False, the beta0 is determined by fitting
    # the circle data.
    #
    # If USE_MEAN_CAMERA_OFFSET=True, the mean camera offset for all sets
    # of measurements is used for all alpha and beta fixpoints. If set to
    # False, every gearbox fit has a camera offset unique to that
    # particular combination of alpha and beta fixpoint.
    # (Only relevant when FIX_CAMERA_OFFSET is False.)
    #
    # If FIX_BETA0=True, the mean beta0 for all sets
    # of measurements is used for all alpha and beta fixpoints. If set to
    # False, every gearbox fit has a beta0 unique to that
    # particular combination of alpha and beta fixpoint.
    # (Only relevant when FIX_BETA0 is False.)
    #
    FIX_CAMERA_OFFSET = True,
    FIX_BETA0 = True,
    USE_MEAN_CAMERA_OFFSET = True,
    USE_MEAN_BETA0 = True,
)

#
# NOTE: The following parameters define a default plate scale which
# is only used if a camera calibration file is not found.
#
# FIXME: The alpha arm radius is averaging at 7.765mm which suggests the platescale should be 0.0242
POS_REP_PLATESCALE = 0.0235  # millimeter per pixel
#POS_REP_PLATESCALE = 0.0242  # millimeter per pixel

# This is the fallback configuration, which is linear scaling.
#
# If available, it is replaced by the distortion-correcting
# calibration which the map file points to.

POS_REP_CALIBRATION_PARS = {"algorithm": "scale", "scale_factor": POS_REP_PLATESCALE}

POS_REP_TARGET_DETECTION_OTSU_PARS = Namespace(
    CALIBRATION_PARS=POS_REP_CALIBRATION_PARS,
    SMALL_RADIUS=SMALL_TARGET_RADIUS,  # in mm
    LARGE_RADIUS=LARGE_TARGET_RADIUS,  # in mm
    GROUP_RANGE=TARGET_SEPERATION,  # in mm
    THRESHOLD_LIMIT=THRESHOLD_LIMIT,
    QUALITY_METRIC=0.4,  # dimensionless
    BLOB_SIZE_TOLERANCE=0.2, # dimensionless
    GROUP_RANGE_TOLERANCE=0.1 # dimensionless
)
POS_REP_TARGET_DETECTION_CONTOUR_PARS = Namespace(
    CALIBRATION_PARS=POS_REP_CALIBRATION_PARS,
    SMALL_DIAMETER=1.45,  # millimeter
    LARGE_DIAMETER=2.45,  # millimeter
    DIAMETER_TOLERANCE=0.15,  # millimeter
    THRESHOLD=70,  # 0-255
    QUALITY_METRIC=0.8,  # dimensionless
)

POS_REP_ANALYSIS_PARS = Namespace(
    CALIBRATION_PARS=POS_REP_CALIBRATION_PARS,
    TARGET_DETECTION_ALGORITHM="otsu",  # "otsu" or "contours"
    TARGET_DETECTION_OTSU_PARS=POS_REP_TARGET_DETECTION_OTSU_PARS,
    TARGET_DETECTION_CONTOURS_PARS=POS_REP_TARGET_DETECTION_CONTOUR_PARS,
    PLATESCALE=POS_REP_PLATESCALE,  # millimeter per pixel
    MAX_FAILURE_QUOTIENT=0.2,
    display=False,
    verbosity=0,
    loglevel=0,
)

#
# Positional verification data collection parameter set.
# ------------------------------------------------------
POS_VER_MEASUREMENT_PARS = Namespace(
    # The rotary stage angle (degree) required to place each FPU under the
    # positional repeatability camera.
    POS_REP_POSITIONS=POS_REP_POSITIONS,
    # The exposure time in milliseconds for a correctly exposed image.
    POS_VER_EXPOSURE_MS=250,
    # Name of the file containing a fixed list of arm positions. Set to None
    # for random positions. File should be in the FPUVerification folder.
    POS_VER_MOTION_FILE = "pos_ver_motion_config",
    # The number of extra random sample points
    POS_VER_ITERATIONS=10,
    # Safety distance (degrees) towards range limits.
    POS_VER_SAFETY_TOLERANCE=1.5,
    POS_VER_CALIBRATION_MAPFILE="calibration/mapping/pos-rep-2019-04-10.cfg",
    
    # Number of datum measurements in before and after a pos_rep measurement.
    N_DATUM=3,
    # The distance (in steps) to move between datum measurements.
    SMALL_MOVE=15,
)


#
# Positional verification data analysis parameter set.
# ----------------------------------------------------
POS_VER_EVALUATION_PARS = Namespace(
    # The maximum angular deviation (degrees) from an average position of
    # a grouping of measured points at a given nominal position which
    # represents an acceptable FPU
    POS_VER_PASS=0.030,
    
    # The following parameters define how the positional verification
    # software recalibrates the orientation of the turntable and camera
    # to derive a new camera offset. The following choices are available.
    #
    # DATUM: Derive the camera offset from datum measurements, assuming
    #        the beta0 offset is known and has not changed. Not recommended
    #        because this seems to make calibration worse, probably because
    #        the assumption that beta0 is correct is wrong.
    #
    # ALPHA: Derive the camera offset using the target location on a series
    #        of alpha circles. If there is more than one alpha circle, the
    #        final camera offset is the average for all the alpha circles.
    #        This technique also assumes the beta0 offset is known and has
    #        not changed, but averaging several alpha circles made at
    #        different beta fixpoints helps to cancel out beta effects.
    #        This setting is the recommended default. It works in most cases.
    #
    # BETA:  Derive the camera offset from the beta axis locations resulting
    #        from a circle fit to a series of beta circles. The change in
    #        location of the beta axis with alpha angle gives the camera offset.
    #        This is the most reliable method for measuring camera offset
    #        because the result is independent of beta0 angle, but it depends
    #        on having a good set of beta circles. If the beta circles have few
    #        points or don't cover a full range of angles there is a danger the
    #        circle fit may not be reliable, in which case ALPHA is a better
    #        choice. Recommended if a good set of beta circles is included.
    #
    # ORIGINAL: Do not attempt to recalibrate the camera offset. Use the
    #        value derived from the gearbox calibration. NOT recommended
    #        because results are affected by turntable movement. Use for
    #        experimental diagnostics only.
    # 
    CAMERA_OFFSET_CHOICES = ("DATUM", "ALPHA", "BETA", "ORIGINAL"),
    #CAMERA_OFFSET_FROM = "DATUM",
    #CAMERA_OFFSET_FROM = "ALPHA",
    CAMERA_OFFSET_FROM = "BETA",
    #CAMERA_OFFSET_FROM = "ORIGINAL",

    # This parameter can be set True to recalibrate the beta0 offset angle
    # from the datum measurements. Setting CAMERA_OFFSET_FROM to "BETA" and
    # RECALIBRATE_BETA0 to True reproduces the same independent calibration
    # used at the gearbox calibration stage when FIX_CAMERA_OFFSET and
    # FIX_BETA0 are both set to True. The recommended value is True, but
    # don't set to True if CAMERA_OFFSET_FROM is also set to "DATUM".
    RECALIBRATE_BETA0 = True,
)


#
# Pupil alignment data collection parameter set.
# ----------------------------------------------
PUP_ALGN_MEASUREMENT_PARS = Namespace(
    # The rotary stage angle required to place each FPU under the first pupil
    # alignment fold mirror.
    PUP_ALGN_POSITIONS=[19, 79, 139, 200, 260],
    # Linear stage positions required to illuminate each FPU fibre
    PUP_ALGN_LINPOSITIONS=LINPOSITIONS,
    # The exposure time in milliseconds for a correctly exposed image
    PUP_ALGN_EXPOSURE_MS=3000,
    
    PUP_ALGN_LAMP_VOLTAGE=5,
    PUP_ALGN_CALIBRATION_MAPFILE="calibration/mapping/pup-aln-2019-04-10.cfg",
)

#
# NOTE: The following parameters define a default plate scale which
# is only used if a camera calibration file is not found.
#
PUP_ALGN_PLATESCALE = 0.76
PUP_ALGN_CALIBRATION_PARS = {"algorithm": "scale", "scale_factor": PUP_ALGN_PLATESCALE}
PUP_ALGN_RADIUS_OF_CURVATURE = 4101.4 # mm

#
# Pupil alignment data analysis parameter set.
# --------------------------------------------
PUP_ALGN_ANALYSIS_PARS = Namespace(
    PLATESCALE=PUP_ALGN_PLATESCALE,  # millimeter per pixel

    MIN_RADIUS=150.0,  # in mm
    MAX_RADIUS=300.0,  # in mm
    THRESHOLD_LIMIT=60,
    QUALITY_METRIC=0.6,  # dimensionless

    PUP_ALGN_CIRCULARITY_THRESH=0.6,  # dimensionless
    PUP_ALGN_NOISE_METRIC=0,
    CALIBRATION_PARS=PUP_ALGN_CALIBRATION_PARS,
    display=False,
    verbosity=0,
    loglevel=0,
)


PUP_ALGN_EVALUATION_PARS = Namespace(
    # The effective radius of curvature of the wavefront from the
    # pupil at the screen (mm).
    CURVATURE=PUP_ALGN_RADIUS_OF_CURVATURE,

    # The maximum total deviation in arcmin from the calibrated centre
    # point which represents an acceptable FPU
    PUP_ALGN_PASS=Inf,  # TBD ??
)


#
# Metrology height data collection parameter set.
# -----------------------------------------------
MET_HEIGHT_MEASUREMENT_PARS = Namespace(
    # The rotary stage angle required to place each FPU in front of the
    # metrology height camera.
    MET_HEIGHT_POSITIONS=[
        269.5,
        330.0,
        28.0,
        88.5,
        148.5,
    ],
    # The exposure time in milliseconds for a correctly exposed image
    # of the illuminated targets.
    MET_HEIGHT_TARGET_EXPOSURE_MS=50,
)

#
# Metrology height data analysis parameter set.
# ---------------------------------------------
MET_HEIGHT_ANALYSIS_PARS = Namespace(
    METHT_PLATESCALE=0.00668,  # millimeter per pixel
    METHT_THRESHOLD=150,  # 0-255
    METHT_SCAN_HEIGHT=2000,  # pixels
    METHT_GAUSS_BLUR=1,  # pixels - MUST BE AN ODD NUMBER
    METHT_STANDARD_DEV=0.1,  # millimeter
    METHT_NOISE_METRIC=0.25, # dimensionless
    display=False,
    verbosity=0,
    loglevel=0,
)

MET_HEIGHT_EVALUATION_PARS = Namespace(
     # Maximum allowable height of both targets, in millimeter.
    MET_HEIGHT_TOLERANCE=Inf # TBD ??
)
