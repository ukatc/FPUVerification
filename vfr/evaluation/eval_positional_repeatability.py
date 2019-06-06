# -*- coding: utf-8 -*-
"""Module to evaluate datum repeatability.

"""
from __future__ import division, print_function

import warnings

import numpy as np
import logging


def get_angular_error(dict_of_coords, idx):
    coords_per_angvec = {}

    for k, v in dict_of_coords.items():
        angvec = (k[0], k[1])
        if not coords_per_angvec.has_key(angvec):
            coords_per_angvec[angvec] = []

        coords_per_angvec[angvec].append(v)

    max_err_at_angle = {}
    for angvec, v in coords_per_angvec.items():
        va = np.array(v)
        avg = np.mean(
            va, axis=0
        )  # this is an average of big and small target coords separately
        err_small = map(np.linalg.norm, va[:, :2] - avg[:2])
        err_big = map(np.linalg.norm, va[:, 2:] - avg[2:])

        # get maximum for both targets
        ang = angvec[idx]
        if ang not in max_err_at_angle:
            max_err_at_angle[ang] = 0

        max_err_at_angle[ang] = max(
            max_err_at_angle[ang], max(np.hstack([err_small, err_big]))
        )
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
