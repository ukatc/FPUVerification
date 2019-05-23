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

    return analysis_func(image_path, pars=func_pars, correct=correct)

def evaluate_datum_repeatability(datumed_coords, moved_coords, pars=None):
    """Takes two lists of (x,y) coordinates : coordinates
    for unmoved FPU, for an FPU which was only datumed, for an FPU which
    was moved, then datumed.

    The units are in millimeter.

    The returned value is the repeatability value in millimeter.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    # get data, omitting quality factors
    xy_datumed = array(datumed_coords)
    xy_moved = array(moved_coords)

    datumed_mean = mean(xy_datumed, axis=0)  # averages small and big targets
    moved_mean = mean(xy_datumed, axis=0)

    datumed_errors_small = map(norm, xy_datumed[:, :2] - datumed_mean[:2])
    datumed_errors_big = map(norm, xy_datumed[:, 2:] - datumed_mean[2:])
    moved_errors_small = map(norm, xy_moved[:, :2] - moved_mean[:2])
    moved_errors_big = map(norm, xy_moved[:, 2:] - moved_mean[2:])

    datumed_errors = hstack([datumed_errors_big, datumed_errors_small])
    moved_errors = hstack([moved_errors_big, moved_errors_small])
    datrep_dat_only_max = max(datumed_errors)
    datrep_dat_only_std = std(datumed_errors)
    datrep_move_dat_max = max(moved_errors)
    datrep_move_dat_std = std(moved_errors)

    return (
        datrep_dat_only_max,
        datrep_dat_only_std,
        datrep_move_dat_max,
        datrep_move_dat_std,
        datumed_errors,
        moved_errors,
    )

def get_angular_error(dict_of_coords, idx):
    coords_per_angvec = {}

    for k, v in dict_of_coords.items():
        angvec = (k[0], k[1])
        if not coords_per_angvec.has_key(angvec):
            coords_per_angvec[angvec] = []

        coords_per_angvec[angvec].append(v)

    max_err_at_angle = {}
    for angvec, v in coords_per_angvec.items():
        va = array(v)
        avg = mean(
            va, axis=0
        )  # this is an average of big and small target coords separately
        err_small = map(norm, va[:, :2] - avg[:2])
        err_big = map(norm, va[:, 2:] - avg[2:])

        # get maximum for both targets
        ang = angvec[idx]
        if ang not in max_err_at_angle:
            max_err_at_angle[ang] = 0

        max_err_at_angle[ang] = max(
            max_err_at_angle[ang],
            max(hstack([err_small,
                        err_big])))
        # this is a maximum of all errors

    poserr_max = max(max_err_at_angle.values())

    return max_err_at_angle, poserr_max

def evaluate_positional_repeatability(
        dict_of_coordinates_alpha, dict_of_coordinates_beta, pars=None
):
    """Takes two dictionaries. The keys of each dictionary
    are the (alpha, beta, i,j,k) coordinates  indices of the positional
    repeateability measurement, with one of the alpha/beta coordinates hold
    fixed.

    The values of the dictionary are a 4-tuple of the metrology target
    coordinates:

    (x_small_tgt, y_small_tgt, x_big_tgt, y_big_tgt).

    The units are always millimeter.

    The returned value are the specified values in millimeter:

    posrep_alpha_max_at_angle – maximum positional error at average
                                  of all points at alpha angle Φ

    posrep_beta_max_at_angle – maximum positional error at average
                                  of all points at beta angle Φ, where
                                  Φ depends on the configurable
                                  parameters in 2.10

    posrep_alpha_max – maximum alpha positional error at any angle

    posrep_beta_max – maximum beta positional error at any angle

    posrep_rss – RSS (Root sum of squares) of POS_REP_ALPHA_MAX and POS_REP_BETA_MAX

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    # transform to lists of measurements for the same coordinates

    posrep_alpha_max_at_angle, posrep_alpha_max = get_angular_error(
        dict_of_coordinates_alpha, 0
    )
    posrep_beta_max_at_angle, posrep_beta_max = get_angular_error(
        dict_of_coordinates_beta, 1
    )

    posrep_rss_mm = rss([posrep_alpha_max, posrep_beta_max])

    return (
        posrep_alpha_max_at_angle,
        posrep_beta_max_at_angle,
        posrep_alpha_max,
        posrep_beta_max,
        posrep_rss_mm,
    )

def evaluate_positional_verification(dict_of_coords, pars=None):
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

    posver_error = {}

    for k, va in dict_of_coords.items():
        count, alpha, beta, = k

        # FIXME: compute somehow nominal coordinates
        warnings.warn("insert computation of nominal target coordinates here")
        x_small, y_small = NaN * alpha, NaN * beta
        x_big, y_big = NaN * alpha, NaN * beta

        # compute difference
        err_small = norm(
            va[:2] - array([alpha, beta])
        )  # pylint: disable=invalid-unary-operand-type
        err_big = norm(
            va[2:] - array([alpha, beta])
        )  # pylint: disable=invalid-unary-operand-type

        posver_error[k] = max(err_small, err_big)

    posver_error_max = max(posver_error.values())

    return (posver_error, posver_error_max)
