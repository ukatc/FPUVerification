from __future__ import print_function, division
from numpy import nan
from ImageAnalysisFuncs.base import ImageAnalysisError
from DistortionCorrection import correct


# exceptions which are raised if image analysis functions fail

class PupilAlignmentAnalysisError(ImageAnalysisError):
    pass

# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

PUPIL_ALIGNMENT_ALGORITHM_VERSION = 0.1


def pupil_alignment_image_analysis(ipath, PUPALGN_CALIBRATION_PARS):
    
    """Takes full path name of an image, and returns ....

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """
    # perform correction with loaded image
    image = correct(image, PUPALGN_CALIBRATION_PARS)

    
    bigtarget_coords = (0.0, 0.0)
    smalltarget_coords = (0.0, 0.0)

    return None




def evaluate_pupil_alignment(dict_of_coordinates, POSITION_REP_PASS=None):
    """
    ...

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    return 0.005






