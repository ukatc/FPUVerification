# -*- coding: utf-8 -*-
"""Module to evaluate positional verification.

"""
from __future__ import division, print_function

from Gearbox.gear_correction import polar2cartesian
from vfr.evaluation.measures import NO_MEASURES, get_errors, get_grouped_errors, group_by_subkeys

import warnings
import numpy as np
import logging


def evaluate_positional_verification(dict_of_coords, pars=None,
                                     x_center=None,
                                     y_center=None,
                                     R_alpha=None,
                                     R_beta_midpoint=None,
                                     BLOB_WEIGHT_FACTOR=None,
                                     **kwargs
):
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


    nominal_angles = [(alpha, beta) for (count, alpha, beta) in dict_of_coords.keys()]
    measured_coords = [ [x] for x in dict_of_coords.values()]
    error_by_angle = {}
    # get measured circle center point from alpha arm
    # calibration
    #
    # IMPORTANT: Keep in mind this center point is ONLY valid as long
    # as the alpha arm is in exactly the same position relative to the
    # camera, so no changes to the camera or verification rig are
    # allowed!
    P0 = np.array([x_center, y_center])

    for key, coords in dict_of_coords.items():
        count, alpha, beta = key
        # compute expected coordinate of observation
        pos_alpha = np.array(polar2cartesian(R_alpha, np.deg2rad(alpha)))
        pos_beta = np.array(polar2cartesian(R_beta_midpoint, np.deg2rad(beta)))
        expected_point = P0 + pos_alpha + pos_beta
        error_by_angle[key] = get_errors([coords], centroid=expected_point, weight_factor=BLOB_WEIGHT_FACTOR).max

    error_measures = get_grouped_errors(
        measured_coords,
        list_of_centroids=nominal_angles,
        weight_factor=BLOB_WEIGHT_FACTOR,
    )
    return error_by_angle, error_measures
