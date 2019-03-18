from __future__ import print_function, division

import cv2
from math import pi, sqrt
from matplotlib import pyplot as plt
from numpy import NaN, mean, std
from numpy.linalg import norm

from ImageAnalysisFuncs.base import ImageAnalysisError
from DistortionCorrection import correct
from vfr.conf import INSTRUMENT_FOCAL_LENGTH


# exceptions which are raised if image analysis functions fail


class PupilAlignmentAnalysisError(ImageAnalysisError):
    pass


# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

PUPIL_ALIGNMENT_ALGORITHM_VERSION = 0.1


def pupalnCoordinates(
    image_path,
    # configurable parameters
    PUP_ALGN_PLATESCALE=0.00668,  # mm per pixel
    PUP_ALGN_CIRCULARITY_THRESH=0.8,  # dimensionless
    PUP_ALGN_NOISE_METRIC=0,
    PUP_ALGN_CALIBRATION_PARS=None,
    verbosity=0,  # a value > 5 will write contour parameters to terminal
    display=False,
):  # will display image with contours annotated

    """reads an image from the pupil alignment camera and returns the
        XY coordinates and circularity of the projected dot in mm
        """

    # Authors: Stephen Watson (initial algorithm March 4, 2019(
    # Johannes Nix (code imported and re-formatted)

    image = cv2.imread(image_path)

    # image processing
    # APPLY DISTORTION CORRECTION
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    pupaln_spot_x = 0
    pupaln_spot_y = 0
    pupaln_quality = 0

    # exceptions
    # scale and straighten the result coordinates

    if PUP_ALGN_CALIBRATION_PARS is None:
        PUP_ALGN_CALIBRATION_PARS = {
            "algorithm": "scale",
            "scale_factor": PUP_ALGN_PLATESCALE,
        }

    pupaln_spot_x, pupaln_spot_y, = correct(
        pupaln_spot_x, pupaln_spot_y, calibration_pars=PUP_ALGN_CALIBRATION_PARS
    )

    return pupaln_spot_x, pupaln_spot_y, pupaln_quality


def evaluate_pupil_alignment(
        dict_of_coordinates,
        PUP_ALGN_CALIBRATED_CENTRE_X=None,
        PUP_ALGN_CALIBRATED_CENTRE_Y=None,
):
    """
    ...

    Any error should be signalled by throwing an Exception of class
    PupilAlignmentAnalysisError, with a string member which describes the problem.

    """

    # group by having the same alpha coordinates
    alpha_dict = {}
    for pos, coord in dict_of_coordinates.items():
        alpha, beta = pos
        if not alpha_dict.has_key(alpha):
            alpha_dict[alpha] = []
        alpha_dict[alpha].append(coord)

    beta_errors = []
    beta_centers = []
    for alpha, bgroup in alpha_dict.items():
        bcoords = array(bgroup)
        bcenter = mean(bcoords, axis=0)
        beta_centers.append(bcenter)
        beta_errors.append(mean(map(norm, boords - bcenter)))

    pupalnBetaErr = mean(beta_errors)

    alpha_center = mean(beta_centers, axis=0)
    pupalnAlphaErr = mean(map(norm, beta_centers - alpha_center))

    xc = norm(
        mean(dict_of_coordinates.values(), axis=0)
        - array((PUP_ALGN_CALIBRATED_CENTRE_X, PUP_ALGN_CALIBRATED_CENTRE_Y))
    )

    # ask Steve Watson what the following means - it is from his spec
    warnings.warn("probably rubbish here")
    pupalnChassisErr = atan(xc / INSTRUMENT_FOCAL_LENGTH)

    pupalnTotalErr = sum([pupalnChassisErr, pupalnAlphaErr, pupalnBetaErr])

    pupalnErrorBars = "TBD"

    return (
        pupalnChassisErr,
        pupalnAlphaErr,
        pupalnBetaErr,
        pupalnTotalErr,
        pupalnErrorBars,
    )
