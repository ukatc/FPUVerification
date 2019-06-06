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
