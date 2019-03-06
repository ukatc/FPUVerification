from __future__ import print_function, division

import cv2
from math import pi, sqrt
from numpy.polynomial import Polynomial
from matplotlib import pyplot as plt
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

def pupalnCoordinates(image_path,
	              #configurable parameters
	              PUPALN_PLATESCALE=0.00668, #mm per pixel
	              PUPALN_CIRCULARITY_THRESH=0.8, #dimensionless
	              PUPALN_NOISE_METRIC=0,
	              PUPALN_CALIBRATION_PARS=None,
	              verbosity=0, # a value > 5 will write contour parameters to terminal
	              display=False): #will display image with contours annotated

        """reads an image from the pupil alignment camera and returns the 
        XY coordinates and circularity of the projected dot in mm
        """

        # Authors: Stephen Watson (initial algorithm March 4, 2019(
        # Johannes Nix (code imported and re-formatted)


	image = cv2.imread(image_path)

	#image processing
	#APPLY DISTORTION CORRECTION
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	
	pupaln_spot_x = 0
	pupaln_spot_y = 0
	pupaln_quality = 0

	#exceptions
        # scale and straighten the result coordinates
        
        if POSREP_CALIBRATION_PARS is None:
            POSREP_CALIBRATION_PARS = { 'algorithm' : 'scale',
                                        'scale_factor' : PUPALN_PLATESCALE }

        pupaln_spot_x, pupaln_spot_y, = correct(pupaln_spot_x, pupaln_spot_y,
                                                calibration_pars=PUPALN_CALIBRATION_PARS)
            
	return pupaln_spot_x, pupaln_spot_y, pupaln_quality




def evaluate_pupil_alignment(dict_of_coordinates, POSITION_REP_PASS=None):
    """
    ...

    Any error should be signalled by throwing an Exception of class
    PupilAlignmentAnalysisError, with a string member which describes the problem.

    """

    return 0.005






