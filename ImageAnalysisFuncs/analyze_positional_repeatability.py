from __future__ import print_function, division
from numpy import nan
from base import ImageAnalysisError


# exceptions which are raised if image analysis functions fail

class DatumRepeatabilityAnalysisError(ImageAnalysisError):
    pass

# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

POSITIONAL_REPEATABILITY_ALGORITHM_VERSION = 0.1


def positional_repeatability_image_analysis(ipath,
                                            POSREP_SMALL_TARGET_DIA_LOWER_THRESH=nan,
                                            POSREP_SMALL_TARGET_DIA_UPPER_THRESH=nan,
                                            POSREP_LARGE_TARGET_DIA_LOWER_THRESH=nan,
                                            POSREP_LARGE_TARGET_DIA_UPPER_THRESH=nan,
                                            POSREP_TARGET_CIRCULARITY_THRESH=nan,
                                            POSREP_THRESHOLD_VAL=nan,
                                            POSREP_PLATESCALE=nan,
                                            POSREP_DISTORTION_MATRIX=nan):
    
    """Takes full path name of an image, and returns the (x, Y) coordinates
    of the fibre in millimeter. The coordinates need only to be relative
    to the camera position."""

    return (0.0, 0.0)


def evaluate_datum_repeatability(unmoved_coords, datumed_coords, moved_coords):
    """Takes three lists of (x,y) coordinates : coordinates
    for unmoved FPU, for an FPU which was only datumed, for an FPU which
    was moved, then datumed.

    The units are in millimeter.

    The returned value is the repeatability value in millimeter.
    
    """

    return 0.005
