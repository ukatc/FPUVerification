# -*- coding: utf-8 -*-
"""

Module to evaluate positional repeatability.

"""
from __future__ import division, print_function
from vfr.evaluation.measures import get_errors, get_grouped_errors, group_by_subkeys


def get_angular_error(dict_of_coords, idx, min_number_points=None):

    kfunc = lambda x: (x[0], x[1])
    coords_per_angvec = group_by_subkeys(dict_of_coords, kfunc)

    max_err_at_angle = {}
    for angvec, coords in coords_per_angvec.items():
        max_err_at_angle[angvec[idx]] = get_errors(coords).max

    poserr_measures = get_grouped_errors(
        coords_per_angvec.values(), min_number_points=min_number_points
    )

    return max_err_at_angle, poserr_measures


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

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    # transform to lists of measurements for the same coordinates

    posrep_alpha_max_at_angle, posrep_alpha_measures = get_angular_error(
        dict_of_coordinates_alpha, 0, min_number_points=pars.MIN_NUMBER_POINTS
    )
    posrep_beta_max_at_angle, posrep_beta_measures = get_angular_error(
        dict_of_coordinates_beta, 1, min_number_points=pars.MIN_NUMBER_POINTS
    )

    return (
        posrep_alpha_max_at_angle,
        posrep_beta_max_at_angle,
        posrep_alpha_measures,
        posrep_beta_measures,
    )
