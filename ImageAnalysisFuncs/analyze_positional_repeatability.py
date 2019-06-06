# -*- coding: utf-8 -*-
"""Module to analyze positional repeatability.

Depending on the supplier parameters this module will either use a blob or a contour algorithim to find the targets.

Created on 20/03/2019

@author: Alan O'Brien
:History:

29 Apr 2019:Initial Creation
"""
from __future__ import division, print_function

import warnings

from numpy import NaN, array, hstack, mean, std
from numpy.linalg import norm
import logging

from ImageAnalysisFuncs.base import ImageAnalysisError, rss
from ImageAnalysisFuncs import target_detection_contours, target_detection_otsu

# version number for analysis algorithm
# (each different result for the same data
# should yield a version number increase)

DATUM_REPEATABILITY_ALGORITHM_VERSION = 0.1

POSITIONAL_REPEATABILITY_ALGORITHM_VERSION = 0.1

POSITIONAL_VERIFICATION_ALGORITHM_VERSION = 0.1

CONTOUR_ALGORITHM = "contour"
OTSU_ALGORITHM = "otsu"


def posrepCoordinates(image_path,pars=None, correct=None):
    """ Reads the image and analyse the location and quality of the targets
     using the chosen algorithm


    :return: A tuple length 6 containing the x,y coordinate and quality factor for the small and large targets
    Where quality is measured by 4 * pi * (area / (perimeter * perimeter)).
    (small_x, small_y, small_qual, big_x, big_y, big_qual)
    """

    if pars.TARGET_DETECTION_ALGORITHM == CONTOUR_ALGORITHM:
        analysis_func = target_detection_contours.targetCoordinates
        func_pars = pars.TARGET_DETECTION_CONTOUR_PARS
    elif pars.TARGET_DETECTION_ALGORITHM == OTSU_ALGORITHM:
        analysis_func = target_detection_otsu.targetCoordinates
        func_pars = pars.TARGET_DETECTION_OTSU_PARS
    else:
        raise ImageAnalysisError("TARGET_DETECTION_ALGORITHM ({}) does not match an algorithm.".format(pars.TARGET_DETECTION_ALGORITHM))

    func_pars.display = pars.display
    func_pars.verbosity = pars.verbosity
    func_pars.loglevel = pars.loglevel
    func_pars.PLATESCALE = pars.PLATESCALE

    return analysis_func(image_path, pars=func_pars, correct=correct)
