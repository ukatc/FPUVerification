# -*- coding: utf-8 -*-
from __future__ import division, print_function

import cv2
from ImageAnalysisFuncs.base import ImageAnalysisError
from ImageAnalysisFuncs import target_detection_contours, target_detection_otsu
from target_detection_otsu import OtsuTargetFindingError

# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

METROLOGY_ANALYSIS_ALGORITHM_VERSION = (1,0,0)

CONTOUR_ALGORITHM = "contour"
OTSU_ALGORITHM = "otsu"


# exceptions which are raised if image analysis functions fail


class MetrologyAnalysisTargetError(ImageAnalysisError):
    pass


class MetrologyAnalysisFibreError(ImageAnalysisError):
    pass


def metcalTargetCoordinates(image_path, pars=None):
    """ Reads the image and analyse the location and quality of the targets
     using the chosen algorithm


    :return: A tuple length 6 containing the x,y coordinate and quality factor for the small and large targets
    Where quality is measured by 4 * pi * (area / (perimeter * perimeter)).
    (small_x, small_y, small_qual, big_x, big_y, big_qual)
    """

    if pars.MET_CAL_TARGET_DETECTION_ALGORITHM == CONTOUR_ALGORITHM:
        analysis_func = target_detection_contours.targetCoordinates
        func_pars = pars.MET_CAL_TARGET_DETECTION_CONTOUR_PARS
    elif pars.MET_CAL_TARGET_DETECTION_ALGORITHM == OTSU_ALGORITHM:
        analysis_func = target_detection_otsu.targetCoordinates
        func_pars = pars.MET_CAL_TARGET_DETECTION_OTSU_PARS
    else:
        raise MetrologyAnalysisTargetError(
            "MET_CAL_ALORITHM ({}) does not match an algorithm.".format(
                pars.POS_REP_AlGORITHM
            )
        )

    func_pars.display = pars.display
    func_pars.verbosity = pars.verbosity
    func_pars.loglevel = pars.loglevel
    func_pars.PLATESCALE = pars.PLATESCALE

    try:
        positions = analysis_func(image_path, func_pars)
    except OtsuTargetFindingError as err:
        raise MetrologyAnalysisTargetError(
            err.message + " from Image {}".format(image_path)
        )

    return positions


def metcalFibreCoordinates(image_path, pars=None):  # configurable parameters

    MET_CAL_PLATESCALE = pars.MET_CAL_PLATESCALE
    MET_CAL_QUALITY_METRIC = pars.MET_CAL_QUALITY_METRIC
    verbosity = pars.verbosity
    display = pars.display

    """reads an image from the metrology calibration camera and returns the
        XY coordinates and Gaussian fit quality of the backlit fibre in mm"""

    # Authors: Stephen Watson (initial algorithm March 4, 2019)
    # Johannes Nix (code imported and re-formatted)

    # pylint: disable=no-member
    image = cv2.imread(image_path)

    # image processing
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    metcal_fibre_x = 0
    metcal_fibre_y = 0
    metcal_fibre_quality = 0

    # exceptions: MetrologyAnalysisFibreError()

    return metcal_fibre_x, metcal_fibre_y, metcal_fibre_quality
