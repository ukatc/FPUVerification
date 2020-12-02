from __future__ import division, print_function

import logging

import cv2
from DistortionCorrection import get_correction_func
from ImageAnalysisFuncs.base import ImageAnalysisError
from ImageAnalysisFuncs import fibre_detection_otsu

# exceptions which are raised if image analysis functions fail


class PupilAlignmentAnalysisError(ImageAnalysisError):
    pass


# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

PUPIL_ALIGNMENT_ALGORITHM_VERSION = (1,0,0)


def pupilCoordinates(image_path, pars=None, correct=None, debugging=False):

    """
    
    reads an image from the pupil alignment camera and returns the
    XY coordinates and circularity of the projected dot in mm
        
    """
    # Authors: Stephen Watson (initial algorithm March 4, 2019(
    # Johannes Nix (code imported and re-formatted)

    logger = logging.getLogger(__name__)
    logger.debug("image %s: processing pupil alignment analysis" % image_path)

    # pylint: disable=no-member
    if correct is None:
        correct = get_correction_func(
                    calibration_pars=pars.CALIBRATION_PARS,
                    platescale=pars.PLATESCALE,
                    loglevel=pars.loglevel,
                  )

#     # Open the image file and attempt to convert it to greyscale.
#     image = cv2.imread(image_path)
#     try:
#         greyscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     except cv2.error as err:
#         raise PupilAlignmentAnalysisError(
#             "OpenCV returned error %s for image %s" % (str(err), path)
#         )

    # Find the largest circle and return coordinates
    (pupil_spot_x, pupil_spot_y, pupil_quality) = \
        fibre_detection_otsu.fibreCoordinates(
            image_path,
            pars=pars,
            correct=correct,
            debugging=debugging
        )

    # exceptions
    # scale and straighten the result coordinates


    pupil_spot_x, pupil_spot_y, = correct(pupil_spot_x, pupil_spot_y)

    return pupil_spot_x, pupil_spot_y, pupil_quality
