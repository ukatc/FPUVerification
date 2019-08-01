# -*- coding: utf-8 -*-
"""Module to evaluate positional verification.

"""
from __future__ import division, print_function

from Gearbox.gear_correction import angle_to_point
from vfr.evaluation.measures import get_errors, get_grouped_errors

import numpy as np


def evaluate_positional_verification(
    dict_of_coords,
    pars=None,
    x_center=None,
    y_center=None,
    R_alpha=None,
    R_beta_midpoint=None,
    alpha0_rad=None,
    coeffs=None,
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

    error_by_angle = {}
    # get measured circle center point from alpha arm
    # calibration
    #
    # IMPORTANT: Keep in mind this center point is ONLY valid as long
    # as the alpha arm is in exactly the same position relative to the
    # camera, so no changes to the camera or verification rig are
    # allowed!
    expected_coords = []
    point_list = []

    deg2rad = np.deg2rad
    print(">>>>>>>>>>>> computing point error values")
    for coords, point_pair in dict_of_coords.items():
        print("-------------")
        # get nominal coordinates
        (idx, alpha_nom_deg, beta_nom_deg) = coords
        alpha_nom_rad, beta_nom_rad = deg2rad(alpha_nom_deg), deg2rad(beta_nom_deg)
        expected_point = angle_to_point(
            alpha_nom_rad,
            beta_nom_rad,
            coeffs=coeffs,
            x_center=x_center,
            y_center=y_center,
            R_alpha=R_alpha,
            R_beta_midpoint=R_beta_midpoint,
            alpha0_rad=alpha0_rad,
            already_corrected=True,
        )

        expected_coords.append(expected_point)
        point_list.append([point_pair])
        error_by_angle[coords] = get_errors(
            [point_pair], centroid=expected_point, weight_factor=BLOB_WEIGHT_FACTOR
        ).max
        print("error_by_angle[%r]=%r" % (coords, error_by_angle[coords]))

    print("############ computing summary statistics")
    error_measures = get_grouped_errors(
        point_list, list_of_centroids=expected_coords, weight_factor=BLOB_WEIGHT_FACTOR
    )
    print("pos ver error_measures=%r" % error_measures)
    return error_by_angle, error_measures
