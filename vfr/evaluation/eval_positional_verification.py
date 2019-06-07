# -*- coding: utf-8 -*-
"""Module to evaluate positional verification.

"""
from __future__ import division, print_function

from vfr.evaluation.measures import NO_MEASURES, get_errors, get_grouped_errors, group_by_subkeys

import warnings
import numpy as np
import logging


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


    nominal_angles = [(alpha, beta) for (count, alpha, beta) in dict_of_coords.keys()]
    measured_coords = [ [x] for x in dict_of_coords.values()]
    error_by_angle = {}
    for key, coords in dict_of_coords.items():
        count, alpha, beta = key
        angle = (alpha, beta)
        error_by_angle[key] = get_errors([coords], centroid=angle).max

    error_measures = get_grouped_errors(measured_coords, list_of_centroids=nominal_angles)
    return error_by_angle, error_measures
