from __future__ import division, print_function

import logging
from math import atan

import cv2
from DistortionCorrection import get_correction_func
from ImageAnalysisFuncs.base import ImageAnalysisError
from numpy import array, mean
from numpy.linalg import norm
import numpy as np
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
        pars=None,
        correct=None,
):

    """reads an image from the pupil alignment camera and returns the
        XY coordinates and circularity of the projected dot in mm
        """

    # Authors: Stephen Watson (initial algorithm March 4, 2019(
    # Johannes Nix (code imported and re-formatted)

    logger = logging.getLogger(__name__)

    # pylint: disable=no-member
    if correct is None:
        correct = get_correction_func(calibration_pars=pars.PUP_ALGN_CALIBRATION_PARS,
                                      platescale=pars.PUP_ALGN_PLATESCALE,
                                      loglevel=pars.loglevel)

    image = cv2.imread(image_path)

    # image processing
    # APPLY DISTORTION CORRECTION
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # FIXME: "gray" is unused

    pupaln_spot_x = 0
    pupaln_spot_y = 0
    pupaln_quality = 0

    # exceptions
    # scale and straighten the result coordinates

    logger.debug("image %s: processing pupil alignment analysis" % image_path)

    pupaln_spot_x, pupaln_spot_y, = correct(pupaln_spot_x, pupaln_spot_y)

    return pupaln_spot_x, pupaln_spot_y, pupaln_quality


def evaluate_pupil_alignment(dict_of_coordinates, pars=None):
    """
    ...

    Any error should be signalled by throwing an Exception of class
    PupilAlignmentAnalysisError, with a string member which describes the problem.

    """

    # group by having the same alpha coordinates
    alpha_dict = {}
    for pos, (x, y, q) in dict_of_coordinates.items():
        alpha, beta = pos
        if not alpha_dict.has_key(alpha):
            alpha_dict[alpha] = []
        alpha_dict[alpha].append((x, y))

    beta_errors = []
    beta_centers = []
    for alpha, bgroup in alpha_dict.items():
        bcoords = array(bgroup)
        bcenter = mean(bcoords, axis=0)
        beta_centers.append(bcenter)
        beta_errors.append(mean(map(norm, bcoords - bcenter)))

    pupalnBetaErr = mean(beta_errors)

    alpha_center = mean(beta_centers, axis=0)
    pupalnAlphaErr = mean(map(norm, beta_centers - alpha_center))

    all_coords = array(dict_of_coordinates.values())[:, :2]
    xc = norm(
        mean(all_coords, axis=0)
        - array((pars.PUP_ALGN_CALIBRATED_CENTRE_X, pars.PUP_ALGN_CALIBRATED_CENTRE_Y))
    )

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


def get_min_quality_pupil(list_of_coords):
    """compute minimum quality from a set of coordinate / quality triple
    pairs, as computed by pupAlgnCoordinates()

    """

    cord_array = array(list_of_coords)
    return np.min(cord_array[:, 2])
