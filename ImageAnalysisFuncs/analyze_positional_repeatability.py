from __future__ import print_function, division
from numpy import nan
from base import ImageAnalysisError


# exceptions which are raised if image analysis functions fail

class RepeatabilityAnalysisError(ImageAnalysisError):
    pass

# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

POSITIONAL_REPEATABILITY_ALGORITHM_VERSION = 0.1
DATUM_REPEATABILITY_ALGORITHM_VERSION = 0.1


def positional_repeatability_image_analysis(ipath,
                                            POSREP_SMALL_TARGET_DIA_LOWER_THRESH=nan,
                                            POSREP_SMALL_TARGET_DIA_UPPER_THRESH=nan,
                                            POSREP_LARGE_TARGET_DIA_LOWER_THRESH=nan,
                                            POSREP_LARGE_TARGET_DIA_UPPER_THRESH=nan,
                                            POSREP_TARGET_CIRCULARITY_THRESH=nan,
                                            POSREP_THRESHOLD_VAL=nan,
                                            POSREP_PLATESCALE=nan,
                                            POSREP_DISTORTION_MATRIX=nan):
    
    """Takes full path name of an image, and returns the (x, Y)
    coordinates of the two metrology targets in millimeter (first the
    big, second the small target). The coordinates need only to be
    relative to the camera position.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    bigtarget_coords = (0.0, 0.0)
    smalltarget_coords = (0.0, 0.0)

    return (bigtarget_coords, smalltarget_coords)


def evaluate_datum_repeatability(unmoved_coords, datumed_coords, moved_coords):
    """Takes three lists of (x,y) coordinates : coordinates
    for unmoved FPU, for an FPU which was only datumed, for an FPU which
    was moved, then datumed.

    The units are in millimeter.

    The returned value is the repeatability value in millimeter.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.
    
    """

    return 0.005



def evaluate_positional_repeatability(dict_of_coordinates, POSITION_REP_PASS=None):
    """Takes a dictionary. The keys of the dictionary
    are the i,j,k indices of the positional repeteability measurement.
    Equal i and k mean equal step counts, and j indicates
    the arm and movement direction of the corresponding arm 
    during measurement.

    The values of the dictionary are a 4-tuple
    (alpha_steps, beta_steps, x_measured_1, y_measured_1, x_measured_2, y_measured_2).

    Here, (alpha_steps, beta_steps) are the angle coordinates given by
    the motor step counts (measured in degrees), and (alpha_measured,
    beta_measured) are the cartesian values of the large (index 1) and
    the small (index 2) target measured from the images taken.


    The units are dimensionless counts (for alpha_steps and beta_steps) 
    and millimeter (for x_measured and y_measured).

    The returned value is the repeatability value in millimeter.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    return 0.005



def evaluate_positional_verification(dict_of_coordinates, POSITION_VER_PASS=None):
    """Takes a dictionary. The keys of the dictionary
    are the i,j,k indices of the positional repeteability measurement.
    Equal i and k mean equal step counts, and j indicates
    the arm and movement direction of the corresponding arm 
    during measurement.

    The values of the dictionary are a 4-tuple
    (alpha_steps, beta_steps, x_measured_1, y_measured_1, x_measured_2, y_measured_2).

    Here, (alpha_steps, beta_steps) are the angle coordinates given by
    the motor step counts (measured in degrees), and (alpha_measured,
    beta_measured) are the cartesian values of the large (index 1) and
    the small (index 2) target measured from the images taken.


    The units are in dimensionless counts (for alpha_steps and beta_steps) 
    and millimeter (for x_measured and y_measured).

    The returned value is the repeatability value in millimeter.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    return 0.005



